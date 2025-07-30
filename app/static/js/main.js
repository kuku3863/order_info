// 通用函数
function formatDate(date) {
    var d = new Date(date),
        month = '' + (d.getMonth() + 1),
        day = '' + d.getDate(),
        year = d.getFullYear();

    if (month.length < 2) month = '0' + month;
    if (day.length < 2) day = '0' + day;

    return [year, month, day].join('-');
}

// 日期选择器初始化
$(document).ready(function() {
    // 为日期输入框添加日期选择器
    if ($.fn.datepicker) {
        $('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true,
            language: 'zh-CN'
        });
    }
    
    // 图片预览
    $(document).on('change', 'input[type="file"]', function() {
        var input = this;
        if (input.files && input.files.length > 0) {
            var previewContainer = $('<div class="row preview-container"></div>');
            $(input).after(previewContainer);
            
            for (var i = 0; i < input.files.length; i++) {
                var file = input.files[i];
                if (!file.type.match('image.*')) {
                    continue;
                }
                
                var reader = new FileReader();
                reader.onload = (function(file) {
                    return function(e) {
                        var col = $('<div class="col-md-3 col-sm-4 col-xs-6"></div>');
                        var thumbnail = $('<div class="thumbnail"></div>');
                        var img = $('<img class="img-responsive">');
                        img.attr('src', e.target.result);
                        img.attr('title', file.name);
                        
                        thumbnail.append(img);
                        col.append(thumbnail);
                        previewContainer.append(col);
                    };
                })(file);
                
                reader.readAsDataURL(file);
            }
        }
    });
    
    // 快速添加订单表单处理
    $('#quickAddForm').on('submit', function(e) {
        e.preventDefault();
        
        var formData = {};
        $(this).serializeArray().forEach(function(item) {
            formData[item.name] = item.value;
        });
        
        $.ajax({
            url: '/quick_add',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                if (response.success) {
                    alert('订单添加成功！');
                    $('#quickAddModal').modal('hide');
                    location.reload();
                } else {
                    alert('添加失败: ' + response.error);
                }
            },
            error: function(xhr) {
                var errorMsg = '添加失败';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                alert(errorMsg);
            }
        });
    });
});