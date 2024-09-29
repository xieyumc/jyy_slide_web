from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import os
import uuid
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
import os
import uuid
from django.conf import settings
from imghdr import what

@csrf_exempt
def upload_image(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image and image.content_type.startswith('image/'):
            # 生成唯一的文件名，防止冲突
            ext = os.path.splitext(image.name)[1]
            filename = uuid.uuid4().hex + ext
            filepath = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)

            # 确保上传目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # 保存文件
            with open(filepath, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            # 返回图片的访问 URL
            url = settings.MEDIA_URL + 'uploads/' + filename
            return JsonResponse({'url': url})
        else:
            return JsonResponse({'error': '无效的文件'}, status=400)
    else:
        return JsonResponse({'error': '不支持的请求方法'}, status=405)


def index(request):
    return render(request, 'index.html')