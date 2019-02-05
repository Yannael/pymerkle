"""
Provides the main class for `proof` objects and related functionalities
"""
import uuid
import time
import json
from .utils import stringify_path


# -------------------------------- Main class --------------------------------


class proof(object):
    """Base class for the ``proof`` object

    Basic purpose of this class is to organize the provided proof data in a nicely formatted dictionary,
    so that they can be handled by the ``validations`` module.

    :param generation:  Should be ``'SUCCESS'`` or ``'FAILURE'`` plus explanation message, according to whether
                        or not a proof path could indeed be generated by the provider Merkle-tree
    :type generation:   str
    :param provider:    uuid of the provider Merkle-tree
    :type provider:     str
    :param hash_type:   Hash type of the provider Merkle-tree
    :type hash_type:    str
    :param security:    Security mode of the provider Merkle-tree
    :type security:     bool
    :param encoding:    Encoding type of the provider Merkle-tree
    :type encoding:     str
    :param proof_index: Position where the validation procedure should start from (provided by the Merkle-tree)
    :type proof_index:  int
    :param proof_path:  Path of signed hashes (provided by the Merkle-tree)
    :type proof_path:   list of (+1/-1, str)

    .. note:: Required Merkle-tree parameters (``hash_type``, ``security`` and ``encoding``) are necessary for
              proof validation (cf. the ``validations`` module)

    :ivar header:                 (*dict*) Contains the keys *uuid*, *generation*, *timestamp*, *creation_moment*,
                                  *provider*, *hash_type*, *encoding*, *security* and *status* (see below)
    :ivar header.uuid:            (*str*) uuid of the proof (time-based)
    :ivar header.generation:      (*bool*) ``True`` or ``False`` according to whether or not a proof path could
                                  indeed be generated by the provider Merkle-tree
    :ivar header.timestamp:       (*str*) Creation moment of the proof (msecs) from the start of time
    :ivar header.creation_moment: (*str*) Creation moment in human readable form
    :ivar header.provider:        (*str*) uuid of the provider Merkle-tree
    :ivar header.hash_type:       (*str*) Hash type of the provider Merkle-tree
    :ivar header.encoding:        (*str*) Encoding type of the provider Merkle-tree
    :ivar header.security:        (*bool*) Security mode of the provider Merkle-tree
    :ivar header.status:          (*bool*) ``True`` resp. ``False`` if the proof was found to be *valid*, resp. *invalid*
                                  after the last validation. If no validation has yet been performed, then it
                                  is ``None``.
    :ivar body:                   (*dict*) Contains the keys *proof_index*, *proof_path*
    :ivar body.proof_index:       (*int*) See the homonymous argument of the constructor
    :ivar body.proof_path:        (*list of (+1/-1, str)*) See the homonymous argument of the constructor
    """

    def __init__(
            self,
            generation,
            provider,
            hash_type,
            security,
            encoding,
            proof_index,
            proof_path):
        self.header = {
            'uuid': str(uuid.uuid1()),    # Time based proof id
            'generation': generation,
            'timestamp': int(time.time()),
            'creation_moment': time.ctime(),
            'provider': provider,
            'hash_type': hash_type,
            'encoding': encoding,
            'security': security,
            'status': None               # Will change to True or False after validation
        }

        self.body = {
            'proof_index': proof_index,
            'proof_path': proof_path
        }

    def __repr__(self):
        """Overrides the default implementation.

        Sole purpose of this function is to easy print info about a proof by just invoking it at console.

        .. warning: Contrary to convention, the output of this implementation is *not* insertible to the ``eval`` function
        """

        return '\n    ----------------------------------- PROOF ------------------------------------\
                \n\
                \n    uuid        : {uuid}\
                \n\
                \n    generation  : {generation}\
                \n\
                \n    timestamp   : {timestamp} ({creation_moment})\
                \n    provider    : {provider}\
                \n\
                \n    hash-type   : {hash_type}\
                \n    encoding    : {encoding}\
                \n    security    : {security}\
                \n\
                \n    proof-index : {proof_index}\
                \n    proof-path  :\
                \n    {proof_path}\
                \n\
                \n    status      : {status}\
                \n\
                \n    -------------------------------- END OF PROOF --------------------------------\
                \n'.format(
            uuid=self.header['uuid'],
            generation=self.header['generation'],
            timestamp=self.header['timestamp'],
            creation_moment=self.header['creation_moment'],
            provider=self.header['provider'],
            hash_type=self.header['hash_type'].upper().replace('_', '-'),
            encoding=self.header['encoding'].upper().replace('_', '-'),
            security='ACTIVATED' if self.header['security'] else 'DEACTIVATED',
            proof_index=self.body['proof_index'] if self.body['proof_index'] is not None else '',
            proof_path=stringify_path(
                signed_hashes=self.body['proof_path']),
            status='UNVALIDATED' if self.header['status'] is None
            else 'VALID' if self.header['status'] is True
            else 'NON VALID')

# ------------------------------ JSON formatting -------------------------

    def serialize(self):
        """ Returns a JSON structure with the proof's current characteristics as key-value pairs

        :rtype: dict
        """
        encoder = proofEncoder()
        return encoder.default(self)

    def JSONstring(self):
        """Returns a nicely stringified version of the proof's JSON serialized form

        .. note:: The output of this function is to be passed into the ``print`` function

        :rtype: str
        """
        return json.dumps(
            self,
            cls=proofEncoder,
            sort_keys=True,
            indent=4)


# ------------------------------- JSON encoders --------------------------


class proofEncoder(json.JSONEncoder):
    """Used implicitly in the JSON serialization of proofs. Extends the built-in
    JSON encoder for data structures.
    """

    def default(self, obj):
        """ Overrides the built-in method of JSON encoders according to the needs of this library
        """
        try:
            uuid = obj.header['uuid']
            generation = obj.header['generation']
            timestamp = obj.header['timestamp']
            creation_moment = obj.header['creation_moment']
            provider = obj.header['provider']
            hash_type = obj.header['hash_type']
            encoding = obj.header['encoding']
            security = obj.header['security']
            proof_index = obj.body['proof_index']
            proof_path = obj.body['proof_path']
            status = obj.header['status']
        except TypeError:
            return json.JSONEncoder.default(self, obj)
        else:
            return {
                'header': {
                    'uuid': uuid,
                    'generation': generation,
                    'timestamp': timestamp,
                    'creation_moment': creation_moment,
                    'provider': provider,
                    'hash_type': hash_type,
                    'encoding': encoding,
                    'security': security,
                    'status': status
                },
                'body': {
                    'proof_index': proof_index,
                    'proof_path': [[sign, hash] for (sign, hash) in proof_path] if proof_path is not None else []
                }
            }
