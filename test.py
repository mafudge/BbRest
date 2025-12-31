from dotenv import load_dotenv
import os

load_dotenv(".env")


from bbrest import BbRest

bb = BbRest(
    os.environ["BB_APPKEY"],
    os.environ["BB_SECRET"],
    os.environ["BB_URL"]
)

print(bb.expiration())