from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8)
    business_name: str = Field(min_length=2, max_length=180)
    customer_type: str = "dental_clinic"
    gstin: str | None = None

class LoginIn(BaseModel): email: EmailStr; password: str
class TokenOut(BaseModel): access_token: str; token_type: str = "bearer"
class UserOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; name:str; email:EmailStr; role:str; organization_id:int|None

class ProductOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; name:str; sku:str; description:str; pack_size:str; unit:str; category_id:int; brand_id:int; supplier_id:int
    market_benchmark_price: Decimal; mrp: Decimal; our_selling_price: Decimal; discount: Decimal; available:int; category_name:str; brand_name:str

class ProductCreate(BaseModel):
    name:str; sku:str; description:str="Professional healthcare procurement item."; pack_size:str="1 unit"; unit:str="unit"
    category_id:int; brand_id:int; supplier_id:int; market_benchmark_price:Decimal; mrp:Decimal|None=None; our_selling_price:Decimal|None=None; supplier_cost:Decimal|None=None; landed_cost:Decimal|None=None; stock:int=0

class PriceUpdate(BaseModel): our_selling_price:Decimal; discount:Decimal=0
class CartItemIn(BaseModel): product_id:int; quantity:int=Field(gt=0, le=10000)
class OrderItemIn(BaseModel): product_id:int; quantity:int=Field(gt=0, le=10000)
class OrderCreate(BaseModel): items:list[OrderItemIn]
