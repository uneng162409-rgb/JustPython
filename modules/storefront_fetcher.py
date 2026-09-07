"""
==========================================================
STOREFRONT FETCHER - SAFE PRODUCTION V2
==========================================================

Purpose:
    Load products directly from Shopee Storefront GraphQL

Features:
    - Fetch products page by page
    - limit = products per page
    - max_pages = hard safety limit
    - max_pages = 1 -> fetch 20 products
    - max_pages = 5 -> fetch up to 100 products
    - max_pages = 10 -> fetch up to 200 products
    - NEVER fetch all products by accident
    - Clear logging
    - Retry support
    - Multiple product images
    - Parse price / discount / sold / rating
    - Return pandas.DataFrame
    - Compatible with STEP A

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


# ----------------------------------------------------------
# SUPPORT BOTH CONFIG STRUCTURES
# ----------------------------------------------------------
#
# Preferred:
#
# step_a:
#   storefront:
#       ...
#
# Fallback:
#
# storefront:
#       ...
#
# This prevents old config files from breaking immediately.
# ----------------------------------------------------------

STEP_A_CFG = CFG.get("step_a", {})

STORE = STEP_A_CFG.get("storefront")

if STORE is None:
    STORE = CFG.get("storefront", {})


# ----------------------------------------------------------
# BASIC VALIDATION
# ----------------------------------------------------------

if not isinstance(STORE, dict):
    raise RuntimeError(
        "❌ STOREFRONT CONFIG INVALID"
    )


if not STORE.get("enabled", True):
    print(
        "⚠️ STOREFRONT DISABLED"
    )


# ==========================================================
# SAFE LIMIT CONFIG
# ==========================================================

# Products per page
LIMIT = int(
    STORE.get("limit", 20)
)


# ----------------------------------------------------------
# HARD SAFETY LIMIT
# ----------------------------------------------------------
#
# IMPORTANT:
#
# max_pages = 1
#     -> 20 products
#
# max_pages = 5
#     -> up to 100 products
#
# max_pages = 10
#     -> up to 200 products
#
# We intentionally DO NOT use 0 as default.
# ----------------------------------------------------------

MAX_PAGES = int(
    STORE.get("max_pages", 1)
)


# Safety validation
if LIMIT <= 0:
    LIMIT = 20


if MAX_PAGES <= 0:
    print(
        "⚠️ max_pages <= 0 detected."
    )
    print(
        "⚠️ SAFE MODE: forcing max_pages = 1"
    )

    MAX_PAGES = 1


# Additional absolute safety cap.
#
# Even if somebody accidentally writes
# max_pages: 999999
# we don't want the fetcher to run forever.

ABSOLUTE_MAX_PAGES = 100

if MAX_PAGES > ABSOLUTE_MAX_PAGES:

    print(
        f"⚠️ max_pages={MAX_PAGES} is too high."
    )

    print(
        f"⚠️ SAFE MODE: limiting to "
        f"{ABSOLUTE_MAX_PAGES} pages."
    )

    MAX_PAGES = ABSOLUTE_MAX_PAGES


# ==========================================================
# API
# ==========================================================

API_URL = (
    "https://collshp.com/api/v3/gql/graphql"
    "?q=StorefrontProductListQuery"
)


# ==========================================================
# LOGGER
# ==========================================================

logger = logging.getLogger(
    "Storefront"
)


if not logger.handlers:

    logger.setLevel(
        logging.INFO
    )

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s : %(message)s",
        "%H:%M:%S"
    )

    handler.setFormatter(
        formatter
    )

    logger.addHandler(
        handler
    )


# ==========================================================
# SESSION
# ==========================================================

session = requests.Session()


# ==========================================================
# RETRY
# ==========================================================

RETRY_COUNT = int(
    STORE.get("retry", 3)
)


retry = Retry(
    total=RETRY_COUNT,
    connect=RETRY_COUNT,
    read=RETRY_COUNT,

    backoff_factor=1,

    status_forcelist=[
        429,
        500,
        502,
        503,
        504
    ],

    allowed_methods=[
        "POST"
    ]
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

URL_SUFFIX = STORE.get(
    "url_suffix",
    ""
)


session.headers.update({

    "accept":
        "application/json, text/plain, */*",

    "content-type":
        "application/json;charset=UTF-8",

    "origin":
        "https://collshp.com",

    "referer":
        f"https://collshp.com/"
        f"{URL_SUFFIX}"
        f"?view=storefront",

    "user-agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/150.0 Safari/537.36",

    "cookie":
        "language=th",

    "x-custom-userid":
        STORE.get(
            "custom_userid",
            ""
        )
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

    return str(
        uuid.uuid4()
    )


def make_device():

    return uuid.uuid4().hex.upper()


# ==========================================================
# BUILD PAYLOAD
# ==========================================================

def build_payload(
    offset=0
):

    return {

        "operationName":
            "StorefrontProductListQuery",

        "query":
            QUERY,

        "variables": {

            "urlSuffix":
                STORE.get(
                    "url_suffix",
                    ""
                ),

            "affiliateMeta": {

                "affiliateId":
                    STORE.get(
                        "affiliate_id",
                        ""
                    ),

                "userId":
                    STORE.get(
                        "user_id",
                        ""
                    )

            },

            "cid":
                STORE.get(
                    "cid",
                    "th"
                ),

            "language":
                STORE.get(
                    "language",
                    "th"
                ),

            "deviceId":
                make_device(),

            "uuId":
                make_uuid(),

            "page": {

                "offset":
                    str(offset),

                "limit":
                    str(LIMIT)

            },

            "sortType":
                "ITEM_POPULAR"
        }
    }


# ==========================================================
# FETCH SINGLE PAGE
# ==========================================================

def fetch_page(
    offset=0
):

    payload = build_payload(
        offset
    )

    logger.info(
        f"Loading offset={offset}"
    )

    response = session.post(

        API_URL,

        json=payload,

        timeout=int(
            STORE.get(
                "timeout",
                20
            )
        )
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
# FETCH PRODUCTS
# ==========================================================

def fetch_all():

    """
    Safely fetch storefront products.

    max_pages controls the maximum number
    of pages that can be downloaded.

    Examples:

        limit=20
        max_pages=1
            -> 20 products

        limit=20
        max_pages=5
            -> up to 100 products

        limit=20
        max_pages=10
            -> up to 200 products

    IMPORTANT:
        This function NEVER automatically
        fetches all 1,700+ products.
    """

    offset = 0

    all_items = []

    page_count = 0

    total_count = None

    logger.info(
        "=================================================="
    )

    logger.info(
        "STOREFRONT FETCH START"
    )

    logger.info(
        f"Products per page : {LIMIT}"
    )

    logger.info(
        f"Maximum pages     : {MAX_PAGES}"
    )

    logger.info(
        f"Maximum products  : {LIMIT * MAX_PAGES}"
    )

    logger.info(
        "=================================================="
    )


    while page_count < MAX_PAGES:

        page_count += 1

        # --------------------------------------------------
        # FETCH
        # --------------------------------------------------

        data = fetch_page(
            offset
        )


        # --------------------------------------------------
        # PARSE RESPONSE
        # --------------------------------------------------

        result = (
            data
            .get("data", {})
            .get(
                "storefrontProductList",
                {}
            )
        )


        items = (
            result.get(
                "itemList"
            )
            or []
        )


        pagination = (
            result.get(
                "pagination"
            )
            or {}
        )


        # --------------------------------------------------
        # TOTAL
        # --------------------------------------------------

        total_count = pagination.get(
            "totalCount"
        )


        has_more = pagination.get(
            "hasMore",
            False
        )


        # --------------------------------------------------
        # ADD ITEMS
        # --------------------------------------------------

        all_items.extend(
            items
        )


        # --------------------------------------------------
        # LOG
        # --------------------------------------------------

        logger.info(
            f"PAGE {page_count}/{MAX_PAGES} | "
            f"Fetched {len(items)} items | "
            f"Total fetched: {len(all_items)}"
            f"/{total_count}"
        )


        # --------------------------------------------------
        # STOP: PAGE LIMIT
        # --------------------------------------------------

        if page_count >= MAX_PAGES:

            logger.info(
                "=================================================="
            )

            logger.info(
                f"MAX PAGES REACHED : {MAX_PAGES}"
            )

            logger.info(
                f"SAFE FETCH STOPPED : "
                f"{len(all_items)} products"
            )

            logger.info(
                "=================================================="
            )

            break


        # --------------------------------------------------
        # STOP: NO MORE DATA
        # --------------------------------------------------

        if not has_more:

            logger.info(
                "NO MORE PRODUCTS AVAILABLE"
            )

            break


        # --------------------------------------------------
        # NEXT OFFSET
        # --------------------------------------------------

        offset += LIMIT


        # --------------------------------------------------
        # POLITE DELAY
        # --------------------------------------------------

        delay = float(
            STORE.get(
                "delay",
                1.0
            )
        )

        if delay > 0:

            actual_delay = (
                delay
                + random.uniform(
                    0,
                    0.5
                )
            )

            time.sleep(
                actual_delay
            )


    return all_items


# ==========================================================
# PARSE ITEM CARD
# ==========================================================

PRICE_DIVISOR = 100000


IMAGE_BASE_URL = (
    "https://down-th.img.susercontent.com/file/"
)


MAX_IMAGES = 10


def parse_item_card(
    raw_item: dict
) -> dict:

    item_card = (
        raw_item.get(
            "itemCard"
        )
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
        asset.get(
            "images"
        )
        or
        (
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

        raw_price = (
            price_info.get(
                "price",
                0
            )
        )

        price = (
            float(raw_price)
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
            data.get(
                "itemid"
            )
            or raw_item.get(
                "itemId"
            ),

        "title":
            asset.get(
                "name"
            )
            or raw_item.get(
                "linkName"
            ),

        "product_link":
            raw_item.get(
                "link"
            ),

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

    raw_items = fetch_all()


    if not raw_items:

        logger.warning(
            "⚠️ NO STOREFRONT PRODUCTS FOUND"
        )

        return pd.DataFrame()


    rows = []

    for item in raw_items:

        try:

            row = parse_item_card(
                item
            )

            rows.append(
                row
            )

        except Exception as e:

            logger.error(
                f"❌ PARSE ITEM FAILED : {e}"
            )


    df = pd.DataFrame(
        rows
    )


    logger.info(
        "=================================================="
    )

    logger.info(
        f"STOREFRONT FEED LOADED : "
        f"{len(df)} rows"
    )

    logger.info(
        "=================================================="
    )


    return df


# ==========================================================
# DEBUG MODE
# ==========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)

    print(
        "🧪 STOREFRONT DEBUG MODE"
    )

    print(
        "🧪 SAFE PAGINATION TEST"
    )

    print("=" * 60)

    print()

    print(
        f"📌 limit      = {LIMIT}"
    )

    print(
        f"📌 max_pages  = {MAX_PAGES}"
    )

    print(
        f"📌 max_items  = {LIMIT * MAX_PAGES}"
    )

    print()

    try:

        df = load_storefront_feed()


        print()

        print(
            f"📦 PRODUCTS : {len(df)}"
        )


        if not df.empty:

            print()

            print(
                df.head()
            )


            print()

            print(
                "📋 COLUMNS:"
            )

            print(
                list(df.columns)
            )


        else:

            print(
                "⚠️ DATAFRAME EMPTY"
            )


        print()

        print(
            "🏁 DEBUG TEST COMPLETE"
        )


    except KeyboardInterrupt:

        print()

        print(
            "🛑 FETCH INTERRUPTED BY USER"
        )

        print(
            "🛑 Program stopped safely."
        )


    except Exception as e:

        print()

        print(
            f"❌ STOREFRONT ERROR : {e}"
        )

        raise