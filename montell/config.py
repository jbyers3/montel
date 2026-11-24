import os
from dataclasses import dataclass
@dataclass(frozen=True)
class VendorConfig:
    base_url: str
    path: str
    token: str
    application: str
    @classmethod
    def from_env(cls, prefix):
        return cls(*(os.getenv(prefix+'_'+key,'') for key in ('URL','PATH','TOKEN')),os.getenv(prefix+'_APPLICATION','default'))
