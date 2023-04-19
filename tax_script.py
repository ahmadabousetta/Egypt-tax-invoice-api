import glob
import json
import os
import sys
import subprocess
import datetime

import numpy as np
import pandas as pd
import requests


def get_token(credentials_file):
    with open(credentials_file) as f:
        lines = f.readlines()
        client_id = lines[0].split()[-1]
        client_secret = lines[1].split()[-1]

    url = "https://id.eta.gov.eg/connect/token"

    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "InvoicingAPI",
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(url, headers=headers, data=payload)

    # Print the response if the script fails to connect
    try:
        token = response.json()["access_token"]
    except:
        print(response.text)
        # Exit script
        sys.exit()

    return token


def upload_doc(invoice):
    # read invoice
    df_main = pd.read_excel(invoice, nrows=1)
    df_main = df_main.loc[0]

    # Always set invoice time to 5 minutes before submission to avoid late submission errors
    # remove next line if you want to use the invoice time in the excel sheet
    df_main["date"] = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    df_main["date"] = df_main["date"].strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )  # 2020-12-31T23:59:59Z

    df_issuer_address = pd.read_excel(
        invoice, header=None, index_col=0, usecols="A:B", skiprows=2, nrows=6
    )
    df_issuer_address = df_issuer_address.T
    df_issuer_address.reset_index(drop=True, inplace=True)
    df_issuer_address = df_issuer_address.loc[0]
    df_receiver_address = pd.read_excel(
        invoice, header=None, index_col=0, usecols="C:D", skiprows=2, nrows=6
    )
    df_receiver_address = df_receiver_address.T
    df_receiver_address.reset_index(drop=True, inplace=True)
    df_receiver_address = df_receiver_address.loc[0]
    df_items = pd.read_excel(invoice, header=9)
    df_totals = df_items.sum()
    numerics = df_items.select_dtypes(include=np.number).columns
    df_items[numerics] = df_items[numerics].round(8).astype(str)
    totalSalesAmount = df_totals["salesTotal"].astype(float).round(8)
    totalDiscountAmount = df_totals["discount"].astype(float).round(8)
    netAmount = df_totals["netTotal"].astype(float).round(8)
    taxTotals = df_totals["Tax"].astype(float).round(8)
    totalAmount = df_totals["totalAmount"].astype(float).round(8)
    invoice_lines = []

    for i, item in df_items.iterrows():
        line = {
            "description": item["description"],
            "itemType": item["itemType"],
            "itemCode": item["itemCode"],
            "unitType": "EA",
            "quantity": float(item["quantity"]),
            "internalCode": item["internalCode"],
            "salesTotal": float(item["salesTotal"]),
            "total": float(item["totalAmount"]),
            "valueDifference": 0,
            "totalTaxableFees": 0,
            "netTotal": float(item["netTotal"]),
            "itemsDiscount": 0,
            "unitValue": {
                "currencySold": "EGP",
                "amountEGP": float(item["unitValue"]),
            },
            "discount": {
                "rate": float(item["Discount Rate %"]),
                "amount": float(item["discount"]),
            },
            "taxableItems": [
                {
                    "taxType": "T1",
                    "amount": float(item["Tax"]),
                    "subType": "V009",
                    "rate": 14,
                }
            ],
        }

        invoice_lines.append(line)

    payload = {
        "documents": [
            {
                "issuer": {
                    "address": {
                        "branchID": str(df_issuer_address["كود الفرع"]),
                        "country": df_issuer_address["الدولة"],
                        "governate": df_issuer_address["المحافظة"],
                        "regionCity": df_issuer_address["المدينة"],
                        "street": df_issuer_address["الشارع"],
                        "buildingNumber": str(df_issuer_address["رقم المبنى"]),
                    },
                    "type": "B",
                    "id": str(df_main["issuerId"]),
                    "name": df_main["issuerName"],  # Max 36
                },
                "receiver": {
                    "address": {
                        "country": df_receiver_address["الدولة"],
                        "governate": df_receiver_address["المحافظة"],
                        "regionCity": df_receiver_address["المدينة"],
                        "street": df_receiver_address["الشارع"],
                        "buildingNumber": str(df_receiver_address["رقم المبنى"]),
                    },
                    "type": "B",
                    "id": str(df_main["receiverId"]),
                    "name": df_main["receiverName"],
                },
                "documentType": "I" if df_main["Inv type"] == 3 else "c",
                "documentTypeVersion": "1.0",
                "dateTimeIssued": df_main["date"],  # 2020-12-31T23:59:59Z
                "taxpayerActivityCode": str(df_main["Activity code"]),
                "internalID": str(df_main["InternalID"]),
                "purchaseOrderReference": str(df_main["PO number"]),
                "invoiceLines": invoice_lines,
                "totalDiscountAmount": totalDiscountAmount,
                "totalSalesAmount": totalSalesAmount,
                "netAmount": netAmount,
                "taxTotals": [{"taxType": "T1", "amount": taxTotals}],
                "totalAmount": totalAmount,
                "extraDiscountAmount": 0,
                "totalItemsDiscountAmount": 0,
            }
        ]
    }

    # dump payload to json file. The c# signer expects a single documnent.
    unsigned_file = "./c#_signer/SourceDocumentJson.json"
    json.dump(
        payload["documents"][0],
        open(unsigned_file, "w", encoding="utf-8"),
        indent=4,
        ensure_ascii=False,
    )

    # run .bat file to sign the json file
    subprocess.run(["c#_signer\SubmitInvoices.bat"])

    # check cades signature. If it's invalid, send without signature
    with open("./c#_signer/Cades.txt", "r") as f:
        signature = f.read()
    if len(signature) < 20:
        print(f"Signature '{signature}' is invalid. Sending without signature.")
        payload["documents"][0]["documentTypeVersion"] = "0.9"
    else:
        # load signed json file
        signed_file = "./c#_signer/FullSignedDocument.json"
        payload = json.load(open(signed_file, "r", encoding="utf-8"))

    url = "https://api.invoicing.eta.gov.eg/api/v1/documentsubmissions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    print(json.dumps(payload))
    print(json.dumps(payload).encode("utf-8"))
    print(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    response = requests.request(
        "POST",
        url,
        headers=headers,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    )
    print(response.text)
    if response.json()["rejectedDocuments"]:
        raise Exception(f"File {file} is rejected.")


if __name__ == "__main__":
    upload_dir = "../upload"
    credentials_file = "tax_api_erp_credentials.txt"
    token = get_token(credentials_file)

    for file in glob.glob(f"{upload_dir}/*.xlsx"):
        print(20 * "*")
        print(f"Trying to upload {file} ...")
        try:
            upload_doc(file)
            os.remove(file)
            print(f"File {file} is uploaded successfully.")
        except Exception as e:
            print(e)
        print(20 * "*")
