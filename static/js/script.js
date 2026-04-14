// JavaScript for Simple HTTP File Server

// 任务管理
const taskList = [];
let taskIdCounter = 0;

// 文件操作函数（全局暴露）
window.deleteFile = deleteFile;
window.renameFile = renameFile;
window.moveFile = moveFile;

document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('fileInput');
    const fileCount = document.getElementById('fileCount');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadForm = document.getElementById('uploadForm');
    const taskListBtn = document.getElementById('taskListBtn');
    const taskListModal = document.getElementById('taskListModal');
    const closeTaskModal = document.getElementById('closeTaskModal');
    const taskListContent = document.getElementById('taskListContent');
    const taskCountBadge = document.getElementById('taskCount');

    let selectedFiles = []; // 存储选中的文件

    // 文件选择处理
    if (fileInput && fileCount && uploadBtn) {
        fileInput.addEventListener('change', function () {
            if (this.files.length > 0) {
                selectedFiles = Array.from(this.files);

                if (selectedFiles.length === 1) {
                    fileCount.textContent = selectedFiles[0].name;
                } else {
                    fileCount.textContent = `已选择 ${selectedFiles.length} 个文件`;
                }
                uploadBtn.disabled = false;
            } else {
                selectedFiles = [];
                fileCount.textContent = '未选择文件';
                uploadBtn.disabled = true;
            }
        });
    }
    // 表单提交 - AJAX上传
    if (uploadForm) {
        uploadForm.addEventListener('submit', function (e) {
            e.preventDefault();
            if (selectedFiles.length === 0) return;

            // 为每个文件创建任务
            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i];
                createUploadTask(file);
            }

            // 重置表单
            fileInput.value = '';
            selectedFiles = [];
            fileCount.textContent = '未选择文件';
            uploadBtn.disabled = true;
        });
    }

    // 任务列表弹窗控制
    if (taskListBtn && taskListModal) {
        taskListBtn.addEventListener('click', function () {
            taskListModal.classList.toggle('show');
        });

        const closeModal = function () {
            taskListModal.classList.remove('show');
        };

        if (closeTaskModal) {
            closeTaskModal.addEventListener('click', closeModal);
        }
    }

    // ESC键关闭弹窗
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && taskListModal) {
            taskListModal.classList.remove('show');
        }
    });

    // 键盘导航增强
    const fileLinks = document.querySelectorAll('.file-link');
    fileLinks.forEach(link => {
        link.setAttribute('tabindex', '0');
        link.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });

    // 事件委托 - 处理任务操作按钮
    if (taskListContent) {
        taskListContent.addEventListener('click', function (e) {
            const target = e.target.closest('[data-action]');
            if (!target) return;

            const taskId = parseInt(target.dataset.taskId);
            const action = target.dataset.action;
            const task = taskList.find(t => t.id === taskId);
            if (!task) return;

            if (action === 'stop') {
                stopUpload(task);
            } else if (action === 'delete') {
                deleteTask(task);
            } else if (action === 'resume') {
                resumeUpload(task);
            }
        });
    }

    // 更新任务计数
    function updateTaskCount() {
        if (taskCountBadge) {
            const activeTasks = taskList.filter(t => t.status !== 'completed' && t.status !== 'error' && t.status !== 'stopped').length;
            if (activeTasks > 0) {
                taskCountBadge.textContent = activeTasks;
            } else {
                taskCountBadge.textContent = '';
            }
        }
    }

    // 创建上传任务
    function createUploadTask(file, startByte = 0) {
        const taskId = ++taskIdCounter;
        const task = {
            id: taskId,
            name: file.name,
            fileName: file.name,
            size: file.size,
            file: file,
            status: 'uploading',
            progress: startByte ? Math.round((startByte / file.size) * 100) : 0,
            uploadedBytes: startByte,
            xhr: null
        };
        taskList.push(task);
        updateTaskCount();
        renderTasks();
        startUpload(task, startByte);
    }

    // 开始上传
    function startUpload(task, startByte = 0) {
        const formData = new FormData();
        const file = task.file;

        if (!file) {
            console.error('Upload failed: file not found in task');
            task.status = 'error';
            task.message = '文件未找到';
            updateTaskCount();
            renderTasks();
            return;
        }

        // 如果是续传，添加Range信息
        if (startByte > 0) {
            // 对于这个简单的服务器，我们不支持真正的断点续传
            // 重新上传整个文件
            startByte = 0;
            task.progress = 0;
            task.uploadedBytes = 0;
        }

        // 使用 File 对象直接上传
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        task.xhr = xhr;

        // 记录上次渲染时间，避免频繁渲染
        let lastRenderTime = 0;

        xhr.upload.addEventListener('progress', function (e) {
            if (e.lengthComputable) {
                const totalUploaded = startByte + e.loaded;
                const percentComplete = Math.round((totalUploaded / file.size) * 100);
                task.progress = Math.min(percentComplete, 100);
                task.uploadedBytes = totalUploaded;
            } else {
                // 如果无法计算进度，使用模拟进度（逐渐增加）
                task.progress = Math.min(task.progress + 5, 90);
            }
            // 节流渲染，避免频繁更新DOM
            const now = Date.now();
            if (now - lastRenderTime > 100) {
                lastRenderTime = now;
                renderTasks();
            }
        });

        xhr.upload.addEventListener('load', function () {
            // 上传完成时确保进度为100%
            task.progress = 100;
            task.uploadedBytes = file.size;
            renderTasks();
        });

        xhr.addEventListener('load', function () {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        task.status = 'completed';
                        task.progress = 100;
                        task.message = '上传成功';
                        task.uploadedPath = response.uploaded_path || null;
                    } else {
                        task.status = 'error';
                        task.message = response.message || '上传失败';
                    }
                } catch (e) {
                    task.status = 'completed';
                    task.progress = 100;
                    task.message = '上传成功';
                }
            } else {
                task.status = 'error';
                task.message = '上传失败: ' + xhr.status;
            }
            task.xhr = null;
            updateTaskCount();
            renderTasks();

            // 如果当前页面是目录，2秒后刷新
            if (task.status === 'completed') {
                setTimeout(() => {
                    location.reload();
                }, 1500);
            }
        });

        xhr.addEventListener('error', function () {
            task.status = 'error';
            task.message = '网络错误';
            task.xhr = null;
            updateTaskCount();
            renderTasks();
        });

        xhr.addEventListener('abort', function () {
            if (task.status !== 'stopped') {
                task.status = 'error';
                task.message = '上传被取消';
                task.xhr = null;
                updateTaskCount();
                renderTasks();
            }
        });

        xhr.open('POST', '/', true);
        xhr.setRequestHeader('Accept', 'application/json');
        if (startByte > 0) {
            xhr.setRequestHeader('Content-Range', `bytes ${startByte}-${file.size - 1}/${file.size}`);
        }
        xhr.send(formData);
    }

    // 停止上传
    function stopUpload(task) {
        if (task.status !== 'uploading' || !task.xhr) return;

        task.xhr.abort();
        task.status = 'stopped';
        task.message = '已暂停';
        task.xhr = null;
        updateTaskCount();
        renderTasks();
    }

    // 恢复上传
    function resumeUpload(task) {
        if (task.status !== 'stopped') return;

        task.status = 'uploading';
        task.message = '';
        updateTaskCount();
        renderTasks();

        // 重新开始上传（从0开始，因为服务器不支持断点续传）
        startUpload(task, 0);
    }

    // 删除任务和文件
    function deleteTask(task) {
        if (task.status === 'uploading' && task.xhr) {
            task.xhr.abort();
        }

        // 如果上传完成，尝试删除文件
        if (task.status === 'completed' || task.uploadedPath) {
            deleteFile(task.name);
        }

        // 从任务列表移除
        const index = taskList.findIndex(t => t.id === task.id);
        if (index !== -1) {
            taskList.splice(index, 1);
        }
        updateTaskCount();
        renderTasks();
    }

    // 删除服务器上的文件
    function deleteFile(filename) {
        const xhr = new XMLHttpRequest();
        xhr.open('DELETE', window.location.pathname + encodeURIComponent(filename), true);
        xhr.setRequestHeader('Accept', 'application/json');
        xhr.send();
        // 不等待响应，直接刷新页面
        setTimeout(() => {
            location.reload();
        }, 500);
    }

    // 渲染任务列表
    function renderTasks() {
        if (!taskListContent) return;

        if (taskList.length === 0) {
            taskListContent.innerHTML = '<div class="no-tasks">暂无上传任务</div>';
            return;
        }

        const noTasks = taskListContent.querySelector('.no-tasks');
        if (noTasks) {
            noTasks.remove();
        }

        taskList.forEach(task => {
            let statusText = '';
            let itemClass = 'task-item';
            let actionButtons = '';

            switch (task.status) {
                case 'uploading':
                    statusText = `上传中 ${task.progress}%`;
                    actionButtons = `
                        <button class="task-action-btn btn-stop" data-action="stop" data-task-id="${task.id}" title="暂停">
                            ⏸︎
                        </button>
                        <button class="task-action-btn btn-delete" data-action="delete" data-task-id="${task.id}" title="删除">
                            🗑
                        </button>
                    `;
                    break;
                case 'stopped':
                    statusText = '已暂停';
                    itemClass += ' error';
                    actionButtons = `
                        <button class="task-action-btn btn-resume" data-action="resume" data-task-id="${task.id}" title="继续">
                            ▶
                        </button>
                        <button class="task-action-btn btn-delete" data-action="delete" data-task-id="${task.id}" title="删除">
                            🗑
                        </button>
                    `;
                    break;
                case 'completed':
                    statusText = '已完成';
                    itemClass += ' completed';
                    actionButtons = `
                        <button class="task-action-btn btn-delete" data-action="delete" data-task-id="${task.id}" title="删除">
                            🗑
                        </button>
                    `;
                    break;
                case 'error':
                    statusText = task.message || '失败';
                    itemClass += ' error';
                    actionButtons = `
                        <button class="task-action-btn btn-resume" data-action="resume" data-task-id="${task.id}" title="重试">
                            🔄
                        </button>
                        <button class="task-action-btn btn-delete" data-action="delete" data-task-id="${task.id}" title="删除">
                            🗑
                        </button>
                    `;
                    break;
            }

            const displayProgress = task.status === 'completed' ? 100 : task.progress;

            if (!task.element) {
                const div = document.createElement('div');
                div.className = itemClass;
                div.dataset.taskId = task.id;
                div.innerHTML = `
                    <div class="task-info">
                        <div class="task-name" title="${escapeHtml(task.name)}">${escapeHtml(task.name)}</div>
                        <div class="task-status-row">
                            <span class="task-status-text"></span>
                            <div class="progress-wrapper">
                                <div class="progress-bar-container">
                                    <div class="progress-bar" style="width: 0%"></div>
                                </div>
                            </div>
                            <div class="progress-text"></div>
                        </div>
                    </div>
                    <div class="task-actions"></div>
                `;
                taskListContent.appendChild(div);
                task.element = div;
                task.lastStatus = null;
            }

            task.element.className = itemClass;
            task.element.querySelector('.task-status-text').textContent = statusText;
            task.element.querySelector('.progress-bar').style.width = `${displayProgress}%`;
            task.element.querySelector('.progress-text').textContent = `${displayProgress}%`;

            if (task.lastStatus !== task.status) {
                task.element.querySelector('.task-actions').innerHTML = actionButtons;
                task.lastStatus = task.status;
            }
        });

        // Ensure tasks that were removed are removed from DOM
        Array.from(taskListContent.children).forEach(child => {
            const taskId = parseInt(child.dataset.taskId);
            if (taskId && !taskList.find(t => t.id === taskId)) {
                child.remove();
            }
        });

        if (taskListContent.children.length === 0) {
            taskListContent.innerHTML = '<div class="no-tasks">暂无上传任务</div>';
        }
    }

    // HTML转义
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});

// ========== 文件操作函数（全局暴露） ==========

/**
 * 删除文件
 * @param {string} filename - 要删除的文件名
 */
function deleteFile(filename) {
    if (!confirm(`确定要删除文件 "${filename}" 吗？`)) {
        return;
    }

    const xhr = new XMLHttpRequest();
    xhr.open('DELETE', window.location.pathname + encodeURIComponent(filename), true);
    xhr.setRequestHeader('Accept', 'application/json');

    xhr.onload = function() {
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            if (response.success) {
                showNotification('成功', response.message, 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showNotification('错误', response.message, 'error');
            }
        } else {
            showNotification('错误', '删除失败', 'error');
        }
    };

    xhr.onerror = function() {
        showNotification('错误', '网络错误', 'error');
    };

    xhr.send();
}

/**
 * 重命名文件
 * @param {string} oldName - 原文件名
 */
function renameFile(oldName) {
    const newNameInput = prompt(`重命名 "${oldName}" 为：`, oldName);
    if (!newNameInput || newNameInput.trim() === oldName) {
        return;
    }

    const newName = newNameInput.trim();

    // 前端简单验证：如果新名称和旧名称相同（忽略大小写），则不处理
    if (newName.toLowerCase() === oldName.toLowerCase()) {
        showNotification('提示', '新文件名与旧文件名相同', 'warning');
        return;
    }

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/rename', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Accept', 'application/json');

    xhr.onload = function() {
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            if (response.success) {
                showNotification('成功', response.message, 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showNotification('错误', response.message, 'error');
            }
        } else {
            showNotification('错误', '重命名失败', 'error');
        }
    };

    xhr.onerror = function() {
        showNotification('错误', '网络错误', 'error');
    };

    xhr.send(JSON.stringify({
        old_name: oldName,
        new_name: newName
    }));
}

/**
 * 移动文件
 * @param {string} filename - 要移动的文件名
 */
function moveFile(filename) {
    // 获取目录列表
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/directories', true);
    xhr.setRequestHeader('Accept', 'application/json');

    xhr.onload = function() {
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            if (response.success) {
                showMoveDialog(filename, response.directories);
            } else {
                showNotification('错误', response.message, 'error');
            }
        } else {
            showNotification('错误', '获取目录列表失败', 'error');
        }
    };

    xhr.onerror = function() {
        showNotification('错误', '网络错误', 'error');
    };

    xhr.send();
}

/**
 * 显示移动文件对话框
 * @param {string} filename - 要移动的文件名
 * @param {string[]} directories - 目录列表
 */
function showMoveDialog(filename, directories) {
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';

    // 创建对话框
    const dialog = document.createElement('div');
    dialog.className = 'move-dialog';

    // 构建目录选项
    let dirOptions = '<option value="">根目录</option>';
    directories.forEach(dir => {
        dirOptions += `<option value="${escapeHtml(dir)}">${escapeHtml(dir)}</option>`;
    });

    dialog.innerHTML = `
        <div class="dialog-header">
            <h3>移动文件</h3>
            <button class="close-btn" onclick="closeMoveDialog()">&times;</button>
        </div>
        <div class="dialog-body">
            <p>将 "<strong>${escapeHtml(filename)}</strong>" 移动到：</p>
            <select id="targetDir" class="dir-select">
                ${dirOptions}
            </select>
            <div class="custom-dir">
                <label>
                    <input type="checkbox" id="useCustomDir"> 自定义目录
                </label>
                <input type="text" id="customDirInput" class="custom-dir-input" placeholder="输入目录路径（如：uploads/2024）" disabled>
            </div>
        </div>
        <div class="dialog-footer">
            <button class="btn btn-secondary" onclick="closeMoveDialog()">取消</button>
            <button class="btn btn-primary" onclick="confirmMove('${escapeHtml(filename)}')">移动</button>
        </div>
    `;

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);

    // 绑定复选框事件
    const checkbox = document.getElementById('useCustomDir');
    const customInput = document.getElementById('customDirInput');
    const select = document.getElementById('targetDir');

    checkbox.addEventListener('change', function() {
        customInput.disabled = !this.checked;
        select.disabled = this.checked;
        if (this.checked) {
            customInput.focus();
        }
    });

    // 点击遮罩关闭
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            closeMoveDialog();
        }
    });
}

/**
 * 关闭移动对话框
 */
function closeMoveDialog() {
    const overlay = document.querySelector('.modal-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * 确认移动文件
 * @param {string} filename - 要移动的文件名
 */
function confirmMove(filename) {
    const checkbox = document.getElementById('useCustomDir');
    let targetDir = '';

    if (checkbox && checkbox.checked) {
        targetDir = document.getElementById('customDirInput').value.trim();
    } else {
        const select = document.getElementById('targetDir');
        if (select) {
            targetDir = select.value;
        }
    }

    if (!targetDir && targetDir !== '') {
        showNotification('提示', '请选择或输入目标目录', 'warning');
        return;
    }

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/move', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Accept', 'application/json');

    xhr.onload = function() {
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            if (response.success) {
                closeMoveDialog();
                showNotification('成功', response.message, 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showNotification('错误', response.message, 'error');
            }
        } else {
            showNotification('错误', '移动失败', 'error');
        }
    };

    xhr.onerror = function() {
        showNotification('错误', '网络错误', 'error');
    };

    xhr.send(JSON.stringify({
        filename: filename,
        target_dir: targetDir
    }));
}

/**
 * 显示通知消息
 * @param {string} title - 标题
 * @param {string} message - 消息内容
 * @param {string} type - 类型：success/error/warning
 */
function showNotification(title, message, type = 'info') {
    // 移除旧的通知
    const oldNotifications = document.querySelectorAll('.notification');
    oldNotifications.forEach(n => n.remove());

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;

    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };

    notification.innerHTML = `
        <span class="notification-icon">${icons[type] || icons.info}</span>
        <div class="notification-content">
            <div class="notification-title">${escapeHtml(title)}</div>
            <div class="notification-message">${escapeHtml(message)}</div>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">&times;</button>
    `;

    document.body.appendChild(notification);

    // 自动消失
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * HTML转义
 * @param {string} text - 原始文本
 * @returns {string} - 转义后的文本
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
