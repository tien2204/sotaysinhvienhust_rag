// Các biến và dữ liệu toàn cục không phụ thuộc vào DOM
let allScholarships = []; 
const faqQuestions = [
    "Làm thế nào để đạt điểm rèn luyện loại Giỏi?",
    "Thông tin về học bổng ở đâu?",
    "Quy trình vay vốn ngân hàng cho sinh viên?",
    "Mô hình đào tạo tích hợp Cử nhân - Kỹ sư hoạt động ra sao?",
    "Điều gì xảy ra nếu có kết quả rèn luyện yếu/kém?",
    "Trường hỗ trợ hướng nghiệp và việc làm như thế nào?",
    "Cần giúp đỡ về tâm lý, học tập thì liên hệ ai?",
    "Cách chuyển sinh hoạt Đảng/Đoàn về trường?",
    "Quy tắc ứng xử qua email là gì?",
    "Làm sao để đăng ký Ký túc xá?"
];

// --- TOÀN BỘ LOGIC TƯƠNG TÁC VỚI TRANG WEB SẼ NẰM TRONG ĐÂY ---
document.addEventListener('DOMContentLoaded', () => {

    // --- DOM Elements ---
    // Khai báo bên trong để đảm bảo các phần tử HTML đã tồn tại
    const sendButton = document.getElementById('send-button');
    const userInput = document.getElementById('user-input');
    const messagesDiv = document.getElementById('messages');
    const faqListDiv = document.getElementById('faq-list');
    const scholarshipButton = document.getElementById('scholarship-button');
    const scholarshipModal = document.getElementById('scholarship-modal');
    const closeModalButton = document.getElementById('close-modal-button');
    const scholarshipListContainer = document.getElementById('scholarship-list-container');
    const scholarshipDetailContainer = document.getElementById('scholarship-detail-container');
    const modalTitle = document.getElementById('modal-title');
    const modalHeader = document.querySelector('.modal-header');

    // --- Functions ---
    // Các hàm này được định nghĩa bên trong để có thể truy cập các biến DOM ở trên một cách an toàn

    async function sendMessage() {
        const question = userInput.value.trim();
        if (question === '') return;

        addMessage(question, 'user-message');
        userInput.value = '';
        const thinkingMessage = addThinkingAnimation();

        try {
            const response = await fetch('http://127.0.0.1:8000/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            });

            if (!response.ok) throw new Error('Lỗi khi kết nối đến backend');

            const data = await response.json();
            thinkingMessage.remove();
            addMessage(marked.parse(data.answer), 'bot-message', true);
        } catch (error) {
            console.error('Lỗi:', error);
            if (thinkingMessage) thinkingMessage.remove();
            addMessage('Xin lỗi, đã xảy ra lỗi. Vui lòng thử lại sau.', 'bot-message');
        }
    }

    function addMessage(text, messageType, isHTML = false) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message', messageType);

        if (isHTML) {
            messageContainer.innerHTML = text;
        } else {
            const p = document.createElement('p');
            p.textContent = text;
            messageContainer.appendChild(p);
        }
        
        messagesDiv.appendChild(messageContainer);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        return messageContainer;
    }

    function addThinkingAnimation() {
        const thinkingContainer = document.createElement('div');
        thinkingContainer.classList.add('message', 'bot-message', 'thinking-animation');
        thinkingContainer.innerHTML = '<i class="fas fa-spinner fa-pulse"></i>';
        messagesDiv.appendChild(thinkingContainer);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        return thinkingContainer;
    }

    function populateFAQs() {
        faqListDiv.innerHTML = ''; // Xóa các item cũ nếu có
        faqQuestions.forEach(question => {
            const faqItem = document.createElement('div');
            faqItem.classList.add('faq-item');
            faqItem.textContent = question;
            faqItem.addEventListener('click', () => {
                userInput.value = question;
                sendMessage();
            });
            faqListDiv.appendChild(faqItem);
        });
    }

    async function fetchAndDisplayScholarships() {
        scholarshipModal.classList.remove('hidden');
        scholarshipListContainer.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-pulse"></i></div>';
        showListView();

        if (allScholarships.length === 0) {
            try {
                const response = await fetch('http://127.0.0.1:8000/scholarships');
                if (!response.ok) throw new Error('Lỗi mạng hoặc server.');
                allScholarships = await response.json();
            } catch (error) {
                console.error('Lỗi khi lấy dữ liệu học bổng:', error);
                scholarshipListContainer.innerHTML = '<p class="error-message">Không thể tải danh sách học bổng. Vui lòng thử lại sau.</p>';
                return;
            }
        }
        renderScholarshipList(allScholarships);
    }

    function renderScholarshipList(scholarships) {
        scholarshipListContainer.innerHTML = '';
        if (scholarships.length === 0) {
            scholarshipListContainer.innerHTML = '<p>Hiện tại không có học bổng nào.</p>';
            return;
        }
        scholarships.forEach(scholarship => {
            const item = document.createElement('div');
            item.classList.add('scholarship-item');
            const deadline = new Date(scholarship.Deadline);
            const isExpired = deadline < new Date();
            item.innerHTML = `
                <div class="scholarship-info">
                    <h3 class="scholarship-title">${scholarship.Title}</h3>
                    <p class="scholarship-meta">
                        <span><i class="fas fa-money-bill-wave"></i> ${scholarship.TotalPrice || 'N/A'}</span>
                        <span class="${isExpired ? 'expired' : ''}">
                            <i class="fas fa-clock"></i> Hạn: ${formatDate(scholarship.Deadline)}
                        </span>
                    </p>
                </div>
                <i class="fas fa-chevron-right"></i>`;
            if (isExpired) item.classList.add('item-expired');
            item.addEventListener('click', () => displayScholarshipDetails(scholarship));
            scholarshipListContainer.appendChild(item);
        });
    }

    function displayScholarshipDetails(scholarship) {
        scholarshipDetailContainer.innerHTML = `
            <div class="detail-header"><h2>${scholarship.Title}</h2></div>
            <div class="detail-meta">
                <p><strong>Loại:</strong> ${scholarship.TypeInfo}</p>
                <p><strong>Giá trị:</strong> ${scholarship.TotalPrice}</p>
                <p><strong>Số lượng:</strong> ${scholarship.Quantity} suất</p>
                <p><strong>Hạn nộp:</strong> ${formatDate(scholarship.Deadline)}</p>
            </div>
            <hr>
            <div class="detail-content">${scholarship.Content}</div>`;
        showDetailView();
    }

    function closeModal() {
        scholarshipModal.classList.add('hidden');
    }

    function showDetailView() {
        scholarshipListContainer.classList.add('hidden');
        scholarshipDetailContainer.classList.remove('hidden');
        modalTitle.textContent = "Chi tiết Học bổng";
        
        if (!document.getElementById('back-to-list-button')) {
            const backButton = document.createElement('button');
            backButton.id = 'back-to-list-button';
            backButton.title = 'Quay lại danh sách';
            backButton.innerHTML = '<i class="fas fa-arrow-left"></i>';
            backButton.addEventListener('click', showListView);
            modalHeader.prepend(backButton);
        }
    }

    function showListView() {
        scholarshipListContainer.classList.remove('hidden');
        scholarshipDetailContainer.classList.add('hidden');
        modalTitle.textContent = "Danh sách Học bổng";
        const backButton = document.getElementById('back-to-list-button');
        if (backButton) backButton.remove();
    }

    function formatDate(dateString) {
        const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
        return new Date(dateString).toLocaleDateString('vi-VN', options);
    }

    // --- Event Listeners & Initial Setup ---
    // Gán sự kiện cho các phần tử đã được đảm bảo tồn tại
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    scholarshipButton.addEventListener('click', fetchAndDisplayScholarships);
    closeModalButton.addEventListener('click', closeModal);
    scholarshipModal.addEventListener('click', (e) => {
        if (e.target === scholarshipModal) closeModal();
    });

    // Khởi tạo các thành phần ban đầu của trang
    populateFAQs();
});