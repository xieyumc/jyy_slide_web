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

from django.shortcuts import render, redirect
from .models import Slide
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt # Ensure this is imported
from .ai_service import get_topic_tree, generate_slide_outline


@login_required
@require_POST
@csrf_exempt
def ai_topic_expand(request):
    keywords = request.POST.get('keywords', '').strip()
    if not keywords:
        return JsonResponse({'error': 'Keywords are required'}, status=400)

    response_data = get_topic_tree(keywords)
    if isinstance(response_data, dict) and 'error' in response_data:
        # Consider specific status codes based on error type if desired later
        # For now, a general 500 for service-side errors.
        # If error indicates API key is missing, 503 might also be suitable.
        return JsonResponse(response_data, status=500) 
    return JsonResponse(response_data)

@login_required
@require_POST
@csrf_exempt
def ai_generate_outline(request):
    topic = request.POST.get('topic', '').strip()
    # existing_content = request.POST.get('existing_content', '') # Optional
    if not topic:
        return JsonResponse({'error': 'Topic is required'}, status=400)

    # Optional: retrieve existing_content if you plan to send it
    # existing_content = request.POST.get('existing_content', '') 
    
    response_data = generate_slide_outline(topic) # Pass existing_content if retrieved

    if isinstance(response_data, dict) and 'error' in response_data:
        return JsonResponse(response_data, status=500)
    
    # If no error, response_data is the list of outline strings
    return JsonResponse({'outline': response_data})


@login_required
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





# slideapp/views.py
@login_required
def index(request):
    # 按照创建时间排序的幻灯片
    slides = Slide.objects.all().order_by('-created_at')  # 按照创建时间降序排序
    return render(request, 'index.html', {'slides': slides})

@login_required
def create_slide(request):
    # 获取当前文件所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 默认内容文件的路径
    default_content_path = os.path.join(current_dir, 'default_content.md')

    # 读取默认内容
    with open(default_content_path, 'r', encoding='utf-8') as f:
        default_content = f.read()

    # 创建新的幻灯片，并设置默认内容
    slide = Slide.objects.create(
        title='未命名',
        content=default_content,
        lock=True
    )

    return redirect('edit_slide', slide_id=slide.id)

@login_required
def edit_slide(request, slide_id):
    slide = Slide.objects.get(id=slide_id)
    return render(request, 'edit_slide.html', {'slide': slide})

@login_required
def delete_slide(request, slide_id):
    slide = get_object_or_404(Slide, id=slide_id)
    slide.delete()
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def toggle_lock(request, slide_id):
    slide = get_object_or_404(Slide, id=slide_id)
    # 切换锁定状态
    slide.lock = not slide.lock
    slide.save()
    return JsonResponse({'status': 'success', 'lock': slide.lock})


def public_slides(request):
    slides = Slide.objects.filter(lock=False).order_by('-created_at')
    return render(request, 'public_slides.html', {'slides': slides})


from django.shortcuts import render, get_object_or_404
from .models import Slide
import tempfile
import os
from .src.converter import converter
from django.conf import settings
import traceback


def public_edit_slide(request, slide_id):
    slide = get_object_or_404(Slide, id=slide_id, lock=False)

    # 转换Markdown为HTML
    slide_html = convert_markdown_to_html(slide.content)

    return render(request, 'public_edit_slide.html', {'slide': slide, 'slide_html': slide_html})


def convert_markdown_to_html(markdown_content):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_md_file_path = os.path.join(temp_dir, 'temp.md')
            with open(temp_md_file_path, 'w', encoding='utf-8') as temp_md_file:
                temp_md_file.write(markdown_content)

            # 调用转换器
            converter(temp_md_file_path)

            output_html_path = os.path.join(temp_dir, 'dist', 'index.html')
            with open(output_html_path, 'r', encoding='utf-8') as html_file:
                html_content = html_file.read()

            html_content = html_content.replace('./static/', '/static/')
            html_content = html_content.replace('./img/', '/static/img/')

            return html_content
    except Exception as e:
        error_message = ''.join(traceback.format_exception_only(type(e), e))
        print(f"转换失败: {error_message}")
        return f"<p>转换失败: {error_message}</p>"