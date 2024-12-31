document.addEventListener('DOMContentLoaded', function() {
    // Profile picture preview
    const pictureInput = document.getElementById('id_profile_picture');
    const picturePreview = document.querySelector('.current-picture');

    if (pictureInput && picturePreview) {
        pictureInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    picturePreview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Resume dropzone
    const dropzone = document.getElementById('dropzone');
    const resumeInput = document.getElementById('id_resume');

    if (dropzone && resumeInput) {
        dropzone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            
            if (e.dataTransfer.files.length) {
                resumeInput.files = e.dataTransfer.files;
                updateResumeDisplay(e.dataTransfer.files[0].name);
            }
        });

        dropzone.addEventListener('click', function() {
            resumeInput.click();
        });

        resumeInput.addEventListener('change', function(e) {
            if (e.target.files.length) {
                updateResumeDisplay(e.target.files[0].name);
            }
        });
    }

    function updateResumeDisplay(filename) {
        const message = dropzone.querySelector('.dz-message');
        if (message) {
            message.textContent = `Selected: ${filename}`;
        }
    }

    // Password change confirmation
    const settingsForm = document.querySelector('form.settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', showPasswordChangeModal);
    }

    function showPasswordChangeModal(e) {
        const passwordInput = document.getElementById('id_password1');
        if (passwordInput && passwordInput.value) {
            e.preventDefault();
            document.getElementById('passwordChangeModal').style.display = 'block';
        }
    }

    // Modal control functions
    window.closeModal = function() {
        document.getElementById('passwordChangeModal').style.display = 'none';
    }

    window.confirmPasswordChange = function() {
        document.querySelector('form.settings-form').submit();
    }
});