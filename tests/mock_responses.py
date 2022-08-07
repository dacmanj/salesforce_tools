from arroyo_salesforce.util import sf_id_checksum, datetime_as_epoch
import string


def fake_id(prefix='001', instance='8X', reserved='0', id_size=6):
    valid_id_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    unique_id = ''.join(random.choice(valid_id_chars) for i in range(id_size)).zfill(9)
    sf_id_15_char = f"{prefix}{instance}{reserved}{unique_id}"
    return f"{sf_id_15_char}{sf_id_checksum(sf_id_15_char)}"


TokenPostResponse = f"""{{
    "access_token": "00D8X000000GCRA!ARUAQGK3OOeO6MYKbIoLEQ2sfg58zjepjuYLVnYNUmqfQuEJHVvNLrhtWF4GmNIjhmZx3ixiTIrbunYMd2876SJSkN9qx6ZA",
    "refresh_token": "5Aep861dBl78hMMobVNxMVZVJg_1Imvvotxch3PHQCkLp4R0AGDVXzpB3jA3R.9dRe5TyimZ_u626vdi7VYzrOA",
    "signature": "/ZvBsEm3q1jpv7emCQyyl3DFQapGSzsq4N6xIq/I8qU=",
    "scope": "refresh_token web openid full",
    "id_token": "eyJraWQiOiIyMzgiLCJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdF9oYXNoIjoiRGNDY28zck1EMkd5WUt1TGdtMGo4QSIsInN1YiI6Imh0dHBzOi8vbG9naW4uc2FsZXNmb3JjZS5jb20vaWQvMDBEOFgwMDAwMDBHQ1JBVUE0LzAwNThYMDAwMDBGYWl1V1FBUiIsImF1ZCI6IjNNVkc5WDRMbkNrZkVWVmoyNWI1X2JKblF2RmtkbkNqYm01T3BNSDNIenQ2QUF3WjVyd25rMU51YV82aE9DV2JBRVcxdmlmekN4N1FmcS5rZDk4bW4iLCJpc3MiOiJodHRwczovL2xvZ2luLnNhbGVzZm9yY2UuY29tIiwiZXhwIjoxNjU5ODMzOTExLCJpYXQiOjE2NTk4MzM3OTF9.g2n_JfGnkH1msgTI4nmps3Pg2EYjI3fJoUYBL74DqWTg1AXEjUU8V0J7eXcSnGq7x3gGJpwXjWMbagi9HrupYOPbtccE77hH3Az5xQ7boY-82R632QjgRQMo3auqfii6bJ0nqItHVGuZkNRvOtd8RQZlFLYi5EU7aVtDx7-KpQBSaqODiMyHAGpeV6gfxnLdCYuUzCt64S_8bcA59WM3cnu6LLS_3ZP3h3Asut9C_PktNybwTZdjQ3jrmT9HqIt4h9r9TREPhkAcJG7FoahXW0JVyNzRc1jGGDe27L81tz2SrBu4_pkAFwYdFpB1QDuCk0vJobteEdB7xBAvqTCrVD_kdzGrq1w7wO-riX7eolfDzCpNveg5IlcV6WBJLZArl5uPe-r7BPO2F1dmkn3xiN9gxq9y51mYJnqtiP5jU0uuaLZhUZBmZNX7fR5FO4kLHIvvqNTpSzlisQqSUQsuruMjuJ6LjwlgmVd_OVLZgF4ORVuJeRFW6wuMl7hCyrLUGopFD1lVWkIV0GY0F7scxJdjqKvo2iFCsMdGIi618ObIv5dCGvo3GNuDi3Ic9gdyF0DmoafTsMD9jSxpyugI7VnYibnfMFrW8XZ1Jo9mBLrE6XgizpefURyUPRHsiqkKdnmCsR_gwG54TDD_cSClqpjTT9al_F0FkUoNj7NyFCE",
    "instance_url": "https://testinstance.my.salesforce.com",
    "id": "https://login.salesforce.com/id/00D8X000000GCRAUA4/0058X00000FaiuWQAR",
    "token_type": "Bearer",
    "issued_at": "{datetime_as_epoch()}"
}}"""
