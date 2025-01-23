from fastapi import APIRouter, Depends
import boa
from api.services.dependencies import get_undy
from utils.undy import UndyContracts
from utils.context import get_account
from pydantic import BaseModel

# Router for legos
router = APIRouter()


class LegoInfo(BaseModel):
    addr: str
    version: int
    lastModified: int
    description: str

    class Config:
        schema_extra = {
            "example": {
                "addr": "0x1234567890123456789012345678901234567890",
                "version": 1,
                "lastModified": 1643673600,
                "description": "Example Lego"
            }
        }


class LegosResponse(BaseModel):
    num_legos: int
    legos: list[LegoInfo]

    class Config:
        schema_extra = {
            "example": {
                "num_legos": 1,
                "legos": [{
                    "addr": "0x1234567890123456789012345678901234567890",
                    "version": 1,
                    "lastModified": 1643673600,
                    "description": "Example Lego"
                }]
            }
        }


@router.get("/", response_model=LegosResponse)
def get_legos(undy: UndyContracts = Depends(get_undy)):
    account = get_account('deployer')
    boa.env.add_account(account)
    num_legos = undy.lego_registry.getNumLegos()
    legos = []
    for i in range(num_legos):
        lego = undy.lego_registry.getLegoInfo(i)
        # Convert Vyper struct to dict for Pydantic
        legos.append(LegoInfo(
            addr=str(lego.addr),
            version=lego.version,
            lastModified=lego.lastModified,
            description=lego.description
        ))

    return LegosResponse(
        num_legos=num_legos,
        legos=legos
    )


@router.get("/{lego_id}", response_model=LegoInfo)
def get_lego(lego_id: int, undy: UndyContracts = Depends(get_undy)):
    boa.env.add_account(get_account('deployer'))
    lego = undy.lego_registry.getLegoInfo(lego_id)
    return LegoInfo(
        addr=str(lego.addr),
        version=lego.version,
        lastModified=lego.lastModified,
        description=lego.description
    )
