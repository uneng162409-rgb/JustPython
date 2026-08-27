"""
==========================================================
Storefront Fetcher Production V2
==========================================================

Purpose:
    Load products directly from Shopee Storefront GraphQL

Features:
    - Fetch products page by page
    - max_pages control for testing
    - max_pages = 0 -> fetch all pages
    - max_pages > 0 -> fetch specified number of pages
    - Parse product information
    - Parse price / discount / sold / rating
    - Parse multiple product images
    - Return pandas.DataFrame

Compatible:
    STEP A
==========================================================
"""

import uuid
import time
import random
import logging

import requests
import pandas as pd

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from modules._bootstrap import load_config


# ==========================================================
# CONFIG
# ==========================================================

CFG = load_config()

# IMPORTANT:
# storefront อยู่ระดับเดียวกับ step_a ใน config.yaml
STORE = CFG.get("storefront", {})

if not STORE:
    raise RuntimeError(
        "❌ STOREFRONT CONFIG NOT FOUND\n"
        "กรุณาตรวจสอบ config.yaml ว่ามี:\n\n"
        "storefront:\n"
        "  enabled: true\n"
        "  url_suffix: \"...\"\n"
        "  affiliate_id: \"...\"\n"
        "  user_id: \"...\"\n"
        "  custom_userid: \"...\"\n"
        "  language: \"th\"\n"
        "  cid: \"th\"\n"
        "  limit: 20\n"
        "  timeout: 20\n"
        "  retry: 3\n"
        "  delay: 1.0\n"
    )


API_URL = (
    "https://collshp.com/api/v3/gql/graphql"
    "?q=StorefrontProductListQuery"
)


# ==========================================================
# LOGGER
# ==========================================================

logger = logging.getLogger("Storefront")

if not logger.handlers:

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s : %(message)s",
        "%H:%M:%S"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)


# ==========================================================
# SESSION
# ==========================================================

session = requests.Session()


retry_count = STORE.get("retry", 3)

retry = Retry(
    total=retry_count,
    connect=retry_count,
    read=retry_count,
    backoff_factor=1,
    status_forcelist=[
        429,
        500,
        502,
        503,
        504
    ],
    allowed_methods=["POST"]
)


adapter = HTTPAdapter(
    max_retries=retry
)


session.mount(
    "https://",
    adapter
)

session.mount(
    "http://",
    adapter
)


# ==========================================================
# HEADERS
# ==========================================================

url_suffix = STORE.get("url_suffix", "")

session.headers.update({

    "accept":
        "application/json, text/plain, */*",

    "content-type":
        "application/json;charset=UTF-8",

    "origin":
        "https://collshp.com",

    "referer":
        f"https://collshp.com/"
        f"{url_suffix}"
        f"?view=storefront",

    "user-agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/150.0 Safari/537.36",

    "cookie":
        "language=th",

    "x-custom-userid":
        STORE.get("custom_userid", "")
})


# ==========================================================
# GRAPHQL QUERY
# ==========================================================

QUERY = """
query StorefrontProductListQuery(
  $urlSuffix: String,
  $keyword: String,
  $sortType: SortType,
  $groupId: Long,
  $linkId: Long,
  $page: LinktreelandingpagePaginationInput,
  $listType: MyCollectionListType,
  $affiliateMeta: AffiliateMetaInput,
  $buyerId: Long,
  $uuId: String,
  $deviceId: String,
  $cid: String,
  $language: String
) {

  storefrontProductList(
    urlSuffix: $urlSuffix
    keyword: $keyword
    sortType: $sortType
    groupId: $groupId
    linkId: $linkId
    page: $page
    listType: $listType
    affiliateMeta: $affiliateMeta
    buyerId: $buyerId
    uuId: $uuId
    deviceId: $deviceId
    cid: $cid
    language: $language
  ) {

    itemList {

      linkId
      link
      linkName
      image
      linkType
      itemId
      isPined
      h5Link
      itemCard

    }

    pagination {

      offset
      limit
      hasMore
      totalCount

    }

  }

}
"""


# ==========================================================
# HELPERS
# ==========================================================

def make_uuid():
    return str(uuid.uuid4())


def make_device():
    return uuid.uuid4().hex.upper()


# ==========================================================
# BUILD PAYLOAD
# ==========================================================

def build_payload(offset=0):

    return {

        "operationName":
            "StorefrontProductListQuery",

        "query":
            QUERY,

        "variables": {

            "urlSuffix":
                STORE.get("url_suffix", ""),

            "affiliateMeta": {

                "affiliateId":
                    STORE.get("affiliate_id", ""),

                "userId":
                    STORE.get("user_id", "")

            },

            "cid":
                STORE.get("cid", "th"),

            "language":
                STORE.get("language", "th"),

            "deviceId":
                make_device(),

            "uuId":
                make_uuid(),

            "page": {

                "offset":
                    str(offset),

                "limit":
                    str(STORE.get("limit", 20))

            },

            "sortType":
                "ITEM_POPULAR"
        }
    }


# ==========================================================
# FETCH SINGLE PAGE
# ==========================================================

def fetch_page(offset=0):

    payload = build_payload(offset)

    logger.info(
        f"Loading offset={offset}"
    )

    response = session.post(
        API_URL,
        json=payload,
        timeout=STORE.get("timeout", 20)
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:

        logger.error(
            data["errors"]
        )

        raise RuntimeError(
            data["errors"]
        )

    return data


# ==========================================================
# FETCH ALL PAGES
# ==========================================================

def fetch_all():

    """
    Fetch storefront products page by page.

    max_pages:

        0
            Fetch all pages.

        >0
            Fetch only the specified number
            of pages.

    Example:

        max_pages: 1
            -> fetch first 20 products

        max_pages: 5
            -> fetch first 100 products

        max_pages: 0
            -> fetch everything
    """

    offset = 0

    all_items = []

    page_count = 0

    max_pages = STORE.get(
        "max_pages",
        0
    )

    limit = STORE.get(
        "limit",
        20
    )

    while True:

        page_count += 1

        data = fetch_page(
            offset
        )

        result = (
            data
            .get("data", {})
            .get("storefrontProductList", {})
        )

        items = (
            result.get("itemList")
            or []
        )

        pagination = (
            result.get("pagination")
            or {}
        )

        all_items.extend(
            items
        )

        total = pagination.get(
            "totalCount",
            0
        )

        has_more = pagination.get(
            "hasMore",
            False
        )

        logger.info(
            f"Fetched {len(items)} items "
            f"(total so far: "
            f"{len(all_items)} / {total})"
        )

        # ==================================================
        # TEST LIMIT
        # ==================================================

        if (
            max_pages > 0
            and page_count >= max_pages
        ):

            logger.info(
                f"TEST LIMIT REACHED : "
                f"{max_pages} page(s)"
            )

            break

        # ==================================================
        # NO MORE DATA
        # ==================================================

        if not has_more:

            logger.info(
                "NO MORE PAGES"
            )

            break

        # ==================================================
        # NEXT PAGE
        # ==================================================

        offset += limit

        # ==================================================
        # DELAY
        # ==================================================

        delay = STORE.get(
            "delay",
            1.0
        )

        if delay > 0:

            time.sleep(
                delay
                + random.uniform(
                    0,
                    0.5
                )
            )

    return all_items


# ==========================================================
# PARSE ITEM CARD
# ==========================================================

PRICE_DIVISOR = 100000

IMAGE_BASE_URL = (
    "https://down-th.img.susercontent.com/file/"
)


# ==========================================================
# MAX IMAGES
# ==========================================================

MAX_IMAGES = 10


def parse_item_card(raw_item: dict) -> dict:

    item_card = (
        raw_item.get("itemCard")
        or {}
    )

    asset = (
        item_card.get(
            "itemCardDisplayedAsset",
            {}
        )
        or {}
    )

    data = (
        item_card.get(
            "itemData",
            {}
        )
        or {}
    )

    price_info = (
        data.get(
            "itemCardDisplayPrice",
            {}
        )
        or {}
    )

    sold_info = (
        data.get(
            "itemCardDisplaySoldCount",
            {}
        )
        or {}
    )

    rating_info = (
        data.get(
            "itemRating",
            {}
        )
        or {}
    )

    # ======================================================
    # IMAGES
    # ======================================================

    image_hashes = (
        asset.get("images")
        or (
            [
                asset["image"]
            ]
            if asset.get("image")
            else []
        )
    )

    image_hashes = image_hashes[
        :MAX_IMAGES
    ]

    # ======================================================
    # PRICE
    # ======================================================

    try:

        price = (
            float(
                price_info.get(
                    "price",
                    0
                )
            )
            / PRICE_DIVISOR
        )

    except (
        TypeError,
        ValueError
    ):

        price = 0

    # ======================================================
    # PRODUCT ROW
    # ======================================================

    row = {

        "itemid":
            data.get("itemid")
            or raw_item.get("itemId"),

        "title":
            asset.get("name")
            or raw_item.get("linkName"),

        "product_link":
            raw_item.get("link"),

        "price":
            price,

        "discount_percentage":
            price_info.get(
                "discount",
                0
            ),

        "item_sold":
            sold_info.get(
                "monthlySoldCount",
                0
            ),

        "shop_rating":
            rating_info.get(
                "ratingStar",
                0
            )
    }

    # ======================================================
    # IMAGE URLS
    # ======================================================

    for i, image_hash in enumerate(
        image_hashes,
        1
    ):

        if not image_hash:
            continue

        row[
            f"image_link_{i}"
        ] = (
            f"{IMAGE_BASE_URL}"
            f"{image_hash}"
        )

    return row


# ==========================================================
# PUBLIC ENTRY POINT
# ==========================================================

def load_storefront_feed() -> pd.DataFrame:

    if not STORE.get("enabled", True):

        logger.warning(
            "⚠️ STOREFRONT DISABLED"
        )

        return pd.DataFrame()

    raw_items = fetch_all()

    rows = [
        parse_item_card(item)
        for item in raw_items
    ]

    df = pd.DataFrame(
        rows
    )

    logger.info(
        f"STOREFRONT FEED LOADED : "
        f"{len(df)} rows"
    )

    return df


# ==========================================================
# DEBUG MODE
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "🧪 STOREFRONT DEBUG MODE"
    )

    print(
        "🧪 Fetching according to "
        "max_pages config"
    )

    print("=" * 60)

    df = load_storefront_feed()

    print()

    print(
        f"📦 PRODUCTS : {len(df)}"
    )

    print()

    if not df.empty:
        print(
            df.head()
        )

    print()

    print(
        "🏁 DEBUG TEST COMPLETE"
    )