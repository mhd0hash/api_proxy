import os
import requests
from flask import Flask, request, Response

app = Flask(__name__)

@app.route('/api/proxy', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def proxy_request():
    # دریافت URL هدف از پارامتر 'url' کوئری
    target_url = request.args.get('url')
    if not target_url:
        return Response("Error: 'url' parameter is required.", status=400)

    # اگر URL با http:// یا https:// شروع نشده بود، پیش‌فرض https را در نظر می‌گیریم
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url

    # ارسال درخواست به URL هدف
    try:
        # گرفتن اطلاعات درخواست اصلی (داده‌ها و هدرها)
        original_request_data = request.get_data()
        headers = request.headers.to_dict()

        # حذف هدرهایی که نباید به سرور مقصد ارسال شوند
        headers.pop('Host', None)
        headers.pop('X-Forwarded-For', None)
        headers.pop('X-Real-IP', None)
        headers.pop('Connection', None)
        headers.pop('Content-Length', None) # این هدر را requests خودش تنظیم می‌کند

        method = request.method

        # ارسال درخواست اصلی به URL هدف
        proxied_response = requests.request(
            method=method,
            url=target_url,
            headers=headers,
            data=original_request_data,
            stream=True # برای مدیریت پاسخ‌های بزرگ یا استریمینگ
        )

        # آماده‌سازی پاسخ از سرور مقصد
        response_data = proxied_response.content
        response_headers = proxied_response.headers.to_dict()

        # حذف هدرهایی که نباید در پاسخ به کلاینت ارسال شوند
        response_headers.pop('Content-Encoding', None)
        response_headers.pop('Transfer-Encoding', None)
        response_headers.pop('Content-Length', None) # این هدر نیز توسط Flask تنظیم می‌شود

        # در صورت نیاز می‌توانید هدرهای CORS را اینجا اضافه کنید
        # response_headers['Access-Control-Allow-Origin'] = '*'

        return Response(
            response_data,
            status=proxied_response.status_code,
            headers=response_headers
        )

    except requests.exceptions.RequestException as e:
        # مدیریت خطاهای اتصال یا مشکلات درخواست
        return Response(f"Error connecting to target URL: {e}", status=502)

# این بخش برای اجرای محلی است. Vercel به روش متفاوتی این را مدیریت می‌کند.
# Vercel از طریق متغیرهای محیطی پورت را مشخص می‌کند.
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) # پورت پیش‌فرض 5000 است اگر PORT تعریف نشده باشد
    app.run(host='0.0.0.0', port=port)
