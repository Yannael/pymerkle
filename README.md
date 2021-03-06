# pymerkle: A Python library for constructing Merkle Trees and validating Proofs
[![Build Status](https://travis-ci.com/FoteinosMerg/pymerkle.svg?branch=master)](https://travis-ci.com/FoteinosMerg/pymerkle)
[![Docs Status](https://readthedocs.org/projects/pymerkle/badge/?version=latest)](http://pymerkle.readthedocs.org)
[![PyPI version](https://badge.fury.io/py/pymerkle.svg)](https://pypi.org/project/pymerkle/)
![Python >= 3.6](https://img.shields.io/badge/python-%3E%3D%203.6-blue.svg)

**Complete documentation can be found at [pymerkle.readthedocs.org](http://pymerkle.readthedocs.org/).**

This library implements a class for _binary balanced_ Merkle-trees (with possibly _odd_ number of leaves) capable of
generating _audit-proofs_, _consistency-proofs_ and _inclusion-tests_. It supports all hash functions
(including _SHA3_ variations) and encoding types, whereas _defense against second-preimage attack_ is by default activated.
It further provides flexible mechanisms for validating the generated proofs and thus easy verification of encrypted data.

It is a *zero dependency* library (with the inessential exception of `tqdm` for displaying progress bars).

## Installation

```bash
pip3 install pymerkle --pre
```

## Quick example

**See also [_Usage_](USAGE.md) and [_API_](API.md)**

```python
from pymerkle import *                    # Import MerkleTree, validateProof and validationReceipt

tree = MerkleTree()                       # Create empty SHA256/UTF-8 Merkle-tree with
                                          # defense against second-preimage attack

# Successively update the Merkle-tree with one hundred records

for i in range(100):
    tree.encryptRecord(bytes('{}-th record'.format(i), 'utf-8'))

# Generate some audit-proofs

p = tree.auditProof(b'12-th record')      # Audit proof based on a given record
q = tree.auditProof(55)                   # Audit-proof based upon the 56-th leaf

# Quick validation of the above proofs

validateProof(target_hash=tree.rootHash(), proof=p) # True
validateProof(target_hash=tree.rootHash(), proof=q) # True

# Store the tree's current state (root-hash and length) for later use

old_hash = tree.rootHash()
sublength = tree.length()

# Further encryption of files and objects

tree.encryptObject({'a': 0, 'b': 1})      # One new leaf storing the digest of the given object
tree.encryptFileContent('path_to_file')   # One new leaf storing the digest of the given file's content
tree.encryptFilePerLog('logs/sample_log') # Encrypt file per log (one new leaf for each line)

# Generate consistency-proof for the state before the above encryptions

r = tree.consistencyProof(old_hash, sublength)

# Validate proof and generate corresponding receipt

validation_receipt = validationReceipt(target_hash=tree.rootHash(), proof=r)
```

## Encryption modes

Encryption of _plain text_ (``string``, ``bytes``, ``bytearray``), _JSON_ objects (``dict``) and _files_ is supported.
Use according to convenience any of the following methods of the ``MerkleTree`` class (all of them invoking internally
  the ``.update()`` method for appending newly created leaves):

``.encryptRecord()``, ``.encryptFileConent()``, ``.encryptFilePerLog()``, ``.encryptObject()``, ``.encryptObjectFromFile()``, ``.encryptFilePerObject()``

See [_API_](API.md) or [_Usage_](USAGE.md) for details about arguments and precise functionality.

## Proof validation

Direct validation of a Merkle-proof is performed usind the ``validateProof()`` function, modifying the status
of the inserted proof appropriately and returning the corresponding boolean. A more elaborate validation
procedure includes generating a receipt with the validation result and storing at will the generated receipt
as a ``.json`` file. This is achieved using the ``validationReceipt``like in the above quick example.

See [_API_](API.md) or [_Usage_](USAGE.md) for details about arguments and precise functionality.

## Exporting and reloading the tree from a file

Given an instance of the ``MekleTree`` class, the minimum required information can be exported using the
``.export()`` method into a ``.json`` file, so that the Merkle-tree can be reloaded in its current state
from that file using the ``.loadFromFile()`` static method. This can be useful for transmitting the tree's
current state to a trusted party or retrieving the tree from a backup file. Reconstruction of the tree
is uniquely determined by the sequence of stored hashes (see the next section _Tree structure_ to understand why).

See [_API_](API.md) or [_Usage_](USAGE.md) for details about arguments and precise functionality.


## Tree structure

Contrary to most implementations, the Merkle-tree is here always _binary balanced_, with all nodes except
for the exterior ones (_leaves_) having _two_ parents. This is achieved as follows: upon appending a block
of new leaves, instead of promoting a lonely leaf to the next level or duplicating it, a *bifurcation* node
gets created **_so that trees with the same number of leaves have always identical structure and input clashes
among growing strategies be avoided_** (independently of the configured hash and encoding types).
This standardization is further crucial for:

- fast generation of consistency-proof paths (based on additive decompositions in decreasing powers of _2_)
- fast recalculation of the root-hash after appending a new leaf, since _only the hashes at the tree's
left-most branch need be recalculated_
- memory efficiency, since the height as well as total number of nodes with respect to the tree's length
is controlled to the minimum. For example, a tree with _9_ leaves has _17_ nodes in the present implementation,
whereas the total number of nodes in the structure described
[**here**](https://crypto.stackexchange.com/questions/22669/merkle-hash-tree-updates) is _20_.

The topology is namely identical to that of a binary _Sekura tree_, depicted in Section 5.4 of
[**this**](https://keccak.team/files/Sakura.pdf) paper. Follow the straightforward algorithm of the
[`MerkleTree.update()`](https://pymerkle.readthedocs.io/en/latest/_modules/pymerkle/tree.html#MerkleTree.update)
method for further insight.

### Deviation from bitcoin specification

In contrast to the [_bitcoin_](https://en.bitcoin.it/wiki/Protocol_documentation#Merkle_Trees) specification
for Merkle-trees, lonely leaves are not duplicated in order for the tree to remain genuinely binary. Instead,
creating bifurcation nodes at the rightmost branch allows the tree to remain balanced upon any update.
As a consequence, even if security against second-preimage attack (see below) were deactivated, the current
implementation is by structure invulnerable to length-extension attacks due to the vulnerability described
[**here**](https://github.com/bitcoin/bitcoin/blob/bccb4d29a8080bf1ecda1fc235415a11d903a680/src/consensus/merkle.cpp)
(reported as [CVE-2012-2459](https://nvd.nist.gov/vuln/detail/CVE-2012-2459)). Using Merkle-trees
without duplicate entries further reduces the risk of bugs in protocols based upon them.


## Defense against second-preimage attack


Defense against second-preimage attack is by default activated. Roughly speaking, it consists in the following security measures:

- Before calculating the hash of a leaf, prepend the corresponding record with the null hexadecimal `0x00`

- Before calculating the hash any interior node, prepend both of its parents' hashes with the unit hexadecimal `0x01`

(See [**here**](https://flawed.net.nz/2018/02/21/attacking-merkle-trees-with-a-second-preimage-attack/) or
[**here**](https://news.ycombinator.com/item?id=16572793) for some insight). In order to deactivate defense against
second-preimage attack, set the ``security`` kwarg equal to ``False`` at construction:

```python
tree = MerkleTree(security=False)
```

Read the [`tests/test_defense.py`](https://github.com/FoteinosMerg/pymerkle/blob/master/tests/test_defense.py) file
inside the project's repository to see how to perform second-preimage attacks against the current implementation.


## Running tests


You need to have installed ``pytest``. From inside the root directory run the command

```shell
pytest tests/
```

to run all tests. This might take up to 2-4 minutes, since crypto parts of the code are tested against all possible
combinations of hash algorithm, encoding type and security mode. You can run only a specific test file, e.g., `test_encryption.py`,
with the command

```shell
pytest tests/test_encryption.py
```
