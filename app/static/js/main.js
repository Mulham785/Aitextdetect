document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');

            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Add active class to clicked tab and corresponding content
            tab.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    // Form submission validation
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', (e) => {
            const activeTab = document.querySelector('.tab.active').getAttribute('data-tab');

            if (activeTab === 'upload') {
                const fileInput = document.getElementById('file');
                if (!fileInput.files.length) {
                    e.preventDefault();
                    alert('Please select a PDF file');
                }
            } else {
                const textInput = document.getElementById('text');
                if (!textInput.value.trim()) {
                    e.preventDefault();
                    alert('Please enter some text');
                }
            }
        });
    }
});