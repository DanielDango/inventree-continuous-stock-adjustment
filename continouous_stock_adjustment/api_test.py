from pint import UnitRegistry

from inventree.api import InvenTreeAPI
from inventree.company import SupplierPart
from inventree.part import Part
from requests import HTTPError

SERVER_ADDRESS = 'http://inventree.localhost/'
MY_USERNAME = 'root'
MY_PASSWORD = 'admin'

api = InvenTreeAPI(SERVER_ADDRESS, username=MY_USERNAME, password=MY_PASSWORD)

ureg = UnitRegistry()
unit_list = api.get("/units/")
for unit in unit_list:
    ureg.define(unit["name"] + " = " + unit["definition"])
def remove_stock(barcode, quantity=0):
    try:
        response = InvenTreeAPI.scanBarcode(api, barcode)
    except HTTPError:
        print("Barcode not found")
        return
    part = Part(api, response["part"]["pk"])
    stock = part.getStockItems()
    if quantity == 0:
        part_unit = part._data["units"]
        sk = stock[0]._data["supplier_part"]
        supplier_part = SupplierPart(api, sk)
        (quant, name) = supplier_part["pack_quantity"].split(" ")
        heathen_unit = ureg.Quantity(float(quant), name)
        quantity = heathen_unit.to(part_unit).magnitude
    item = stock[0]
    for item in stock:
        if item._data["quantity"] >= quantity:
            item.removeStock(quantity)
            return
        remainder = quantity - item._data["quantity"]
        item.removeStock(quantity)
        quantity = remainder


part = Part(api, 17)
stock = part.getStockItems()
remove_stock("3", 4)
