// Các biến và dữ liệu toàn cục không phụ thuộc vào DOM
let allScholarships = []; 
const API_BASE_URL = "http://127.0.0.1:8000";
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

// Biến toàn cục để quản lý việc phát âm thanh
let audioPlayer = new Audio();
let currentlyPlayingIcon = null;

// Hàm gọi API để chuyển văn bản thành giọng nói và phát
async function playText(text, iconElement) {
    // Nếu đang có audio khác phát, dừng lại
    if (!audioPlayer.paused) {
        audioPlayer.pause();
        if (currentlyPlayingIcon) {
            currentlyPlayingIcon.className = 'fas fa-volume-up';
        }
        // Nếu click vào chính nút đang phát -> chỉ dừng lại
        if (currentlyPlayingIcon === iconElement) {
            currentlyPlayingIcon = null;
            return;
        }
    }

    currentlyPlayingIcon = iconElement;
    iconElement.className = 'fas fa-spinner fa-pulse'; // Hiển thị trạng thái đang tải

    try {
        const response = await fetch(`${API_BASE_URL}/tts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) {
            throw new Error('Lỗi khi tạo file âm thanh.');
        }

        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);

        audioPlayer.src = audioUrl;
        audioPlayer.play();

        // Cập nhật icon khi bắt đầu phát
        audioPlayer.onplaying = () => {
            iconElement.className = 'fas fa-stop-circle'; // Icon dừng
        };

        // Reset icon khi phát xong
        audioPlayer.onended = () => {
            iconElement.className = 'fas fa-volume-up';
            currentlyPlayingIcon = null;
        };

        // Reset icon nếu có lỗi
        audioPlayer.onerror = () => {
            iconElement.className = 'fas fa-volume-up';
            currentlyPlayingIcon = null;
            console.error("Lỗi khi phát file âm thanh.");
        }

    } catch (error) {
        console.error("Lỗi TTS:", error);
        iconElement.className = 'fas fa-volume-up'; // Reset icon khi có lỗi
        currentlyPlayingIcon = null;
    }
}

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
    
    // Job model element
    const jobsButton = document.getElementById('jobs-button');
    const jobsModal = document.getElementById('jobs-modal');
    const closeJobsModalButton = document.getElementById('close-jobs-modal-button');
    const filterJobsButton = document.getElementById('filter-jobs-button');
    const jobListView = document.getElementById('job-list-view');
    const jobListContainer = document.getElementById('job-list-container');
    const jobDetailContainer = document.getElementById('job-detail-container');
    const careerFilter = document.getElementById('career-filter');
    const cityFilter = document.getElementById('city-filter');
    const jobsModalTitle = document.getElementById('jobs-modal-title');
    const jobsModalHeader = jobsModal.querySelector('.modal-header');

    const activityButton = document.getElementById('activity-button');
    const activityModal = document.getElementById('activity-modal');
    const closeActivityModalButton = document.getElementById('close-activity-modal-button');
    const activityListContainer = document.getElementById('activity-list-container');
    const activityDetailContainer = document.getElementById('activity-detail-container');
    const activityModalTitle = document.getElementById('activity-modal-title');
    const activityModalHeader = activityModal.querySelector('.modal-header');

    // --- Functions ---
    // Các hàm này được định nghĩa bên trong để có thể truy cập các biến DOM ở trên một cách an toàn
    // Hàm helper để định dạng ngày giờ
    function formatDateTime(dateTimeString) {
        if (!dateTimeString) return "N/A";
        try {
            const date = new Date(dateTimeString);
            if (isNaN(date.getTime())) return dateTimeString;
            const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
            return date.toLocaleString('vi-VN', options).replace(',', '');
        } catch (e) {
            return dateTimeString;
        }
    }

    function formatDateTimeRange(start, end) {
        if (!start || !end) return "N/A";
        return `${formatDateTime(start)} - ${formatDateTime(end)}`;
    }

    async function openActivityModal() {
        activityModal.classList.remove('hidden');
        showActivityListView();
        await fetchAndDisplayActivities();
    }

    async function fetchAndDisplayActivities() {
        activityListContainer.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-pulse"></i></div>';
        try {
            const response = await fetch(`${API_BASE_URL}/activities`);
            if (!response.ok) throw new Error('Không thể tải dữ liệu hoạt động.');
            const activities = await response.json();
            renderActivityList(activities);
        } catch (error) {
            console.error("Lỗi khi tải hoạt động:", error);
            activityListContainer.innerHTML = `<p class="error-message">${error.message}</p>`;
        }
    }

    function renderActivityList(activities) {
        activityListContainer.innerHTML = '';
        if (activities.length === 0) {
            activityListContainer.innerHTML = '<p>Không có hoạt động nào sắp diễn ra.</p>';
            return;
        }

        activities.forEach(activity => {
            const item = document.createElement('div');
            item.classList.add('activity-card');
            item.innerHTML = `
                <img class="activity-card-img" src="${activity.image_url || 'https://via.placeholder.com/100x70?text=Event'}" alt="Ảnh hoạt động">
                <div class="activity-card-content">
                    <span class="activity-card-type">${activity.activity_type}</span>
                    <h3 class="activity-card-title">${activity.title}</h3>
                    <p class="activity-card-organizer"><i class="fas fa-user-friends"></i> ${activity.organizer}</p>
                    <p class="activity-card-time"><i class="fas fa-clock"></i> ${formatDateTime(activity.start_time)}</p>
                </div>
            `;
            item.addEventListener('click', () => displayActivityDetails(activity.id));
            activityListContainer.appendChild(item);
        });
    }

    async function displayActivityDetails(activityId) {
        showActivityDetailView();
        // Hiển thị spinner trong khi tải dữ liệu chi tiết
        activityDetailContainer.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-pulse"></i></div>';

        try {
            // GỌI API MỚI ĐỂ LẤY DỮ LIỆU CHI TIẾT
            const response = await fetch(`${API_BASE_URL}/activities/${activityId}`);
            if (!response.ok) throw new Error('Không thể tải chi tiết hoạt động.');
            const activity = await response.json();

            // Xử lý và hiển thị danh sách tiêu chí
            const criteriaHtml = activity.criteria && activity.criteria.length > 0
                ? activity.criteria.map(c => `<li class="criteria-item">${c}</li>`).join('')
                : '<li>Không có thông tin tiêu chí cụ thể.</li>';

            activityDetailContainer.innerHTML = `
                <div class="activity-detail-grid">
                    <div class="activity-detail-left">
                        <img class="activity-detail-img" src="${activity.image_url || 'https://via.placeholder.com/300x150?text=Event'}" alt="Ảnh hoạt động">
                        <h2 class="activity-detail-title">${activity.title}</h2>
                        <div class="activity-meta-list">
                            <div class="activity-meta-item"><span>Địa điểm:</span><p>${activity.location}</p></div>
                            <div class="activity-meta-item"><span>Thời gian:</span><p>${formatDateTimeRange(activity.start_time, activity.finish_time)}</p></div>
                            <div class="activity-meta-item"><span>BTC:</span><p>${activity.organizer}</p></div>
                            <div class="activity-meta-item"><span>Hạn nộp MC:</span><p class="deadline-highlight">${formatDateTime(activity.registration_deadline)}</p></div>
                        </div>
                        <div class="activity-criteria-card">
                            <div class="content-tabs"><button class="tab-button active">Tiêu chí</button></div>
                            <ul class="criteria-content">${criteriaHtml}</ul>
                        </div>
                    </div>
                    <div class="activity-detail-right">
                        <div class="content-tabs"><button class="tab-button active">Nội dung</button></div>
                        <div class="detail-content">${activity.description || '<p>Không có thông tin.</p>'}</div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error("Lỗi khi tải chi tiết hoạt động:", error);
            activityDetailContainer.innerHTML = `<p class="error-message">${error.message}</p>`;
        }
    }



    function closeActivityModal() {
        activityModal.classList.add('hidden');
    }

    function showActivityDetailView() {
        activityListContainer.classList.add('hidden');
        activityDetailContainer.classList.remove('hidden');
        activityModalTitle.textContent = "Chi tiết Hoạt động";

        if (!document.getElementById('activity-back-button')) {
            const backButton = document.createElement('button');
            backButton.id = 'activity-back-button';
            backButton.title = 'Quay lại';
            backButton.innerHTML = '<i class="fas fa-arrow-left"></i>';
            backButton.addEventListener('click', showActivityListView);
            activityModalHeader.prepend(backButton);
        }
    }

    function showActivityListView() {
        activityListContainer.classList.remove('hidden');
        activityDetailContainer.classList.add('hidden');
        activityModalTitle.textContent = "Hoạt động & Sự kiện";
        const backButton = document.getElementById('activity-back-button');
        if (backButton) backButton.remove();
    }

    async function sendMessage() {
        const question = userInput.value.trim();
        if (question === '') return;

        addMessage(question, 'user-message');
        userInput.value = '';
        const thinkingMessage = addThinkingAnimation();

        try {
            const response = await fetch(`${API_BASE_URL}/ask`, {
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

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');

        if (isHTML) {
            messageContent.innerHTML = text;
        } else {
            const p = document.createElement('p');
            p.textContent = text;
            messageContent.appendChild(p);
        }

        messageContainer.appendChild(messageContent);

        // Thêm nút đọc văn bản cho tin nhắn của bot
        if (messageType === 'bot-message' && text.trim() !== '') {
            const speakerButton = document.createElement('button');
            speakerButton.classList.add('speak-button');
            speakerButton.title = 'Đọc văn bản';
            speakerButton.innerHTML = '<i class="fas fa-volume-up"></i>';

            // Lấy nội dung text thuần túy để đọc, tránh đọc các thẻ HTML
            const textToSpeak = messageContent.textContent || messageContent.innerText;

            speakerButton.onclick = () => playText(textToSpeak, speakerButton.querySelector('i'));

            messageContainer.appendChild(speakerButton);
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

    async function openJobsModal() {
        jobsModal.classList.remove('hidden');
        showJobListView();
        
        // Chỉ tải bộ lọc một lần đầu tiên
        if (careerFilter.options.length <= 1) {
            await populateCareerFilter();
        }
        if (cityFilter.options.length <= 1) {
            await populateCityFilter();
        }

        // Tự động tìm kiếm việc làm mới khi mở modal
        fetchAndDisplayJobs();
    }

    async function populateCareerFilter() {
        try {
            const response = await fetch(`${API_BASE_URL}/jobs/careers`);
            const careers = await response.json();
            careers.forEach(career => {
                const option = document.createElement('option');
                option.value = career;
                option.textContent = career;
                careerFilter.appendChild(option);
            });
        } catch (error) {
            console.error("Lỗi khi tải danh sách chuyên ngành:", error);
        }
    }

    async function populateCityFilter() {
        try {
            const response = await fetch(`${API_BASE_URL}/jobs/cities`);
            const cities = await response.json();
            cities.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                cityFilter.appendChild(option);
            });
        } catch (error) {
            console.error("Lỗi khi tải danh sách thành phố:", error);
        }
    }

    async function fetchAndDisplayJobs() {
        jobListContainer.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-pulse"></i></div>';
        
        // 1. Lấy các giá trị từ bộ lọc
        const jobType = document.querySelector('input[name="job-type"]:checked').value;
        const career = careerFilter.value;
        const city = cityFilter.value;

        // 2. Xây dựng URL với các tham số
        const params = new URLSearchParams({ job_type: jobType });
        if (career) {
            params.append('career', career);
        }
        if (city) {
            params.append('city', city);
        }
        
        const url = `${API_BASE_URL}/jobs?${params.toString()}`;
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Không thể tải dữ liệu việc làm.');
            const jobs = await response.json();
            renderJobList(jobs);
        } catch(error) {
            console.error("Lỗi khi tìm kiếm việc làm:", error);
            jobListContainer.innerHTML = `<p class="error-message">${error.message}</p>`;
        }
    }

    function renderJobList(jobs) {
        jobListContainer.innerHTML = '';
        if (jobs.length === 0) {
            jobListContainer.innerHTML = '<p style="text-align: center; padding: 20px;">Không tìm thấy việc làm nào phù hợp.</p>';
            return;
        }

        jobs.forEach(job => {
            const item = document.createElement('div');
            item.classList.add('job-card'); // Sử dụng class mới là job-card

            // Thêm logo công ty (dùng placeholder) và nội dung chính
            item.innerHTML = `
                <div class="job-logo">
                    

    <div class="logo-placeholder">${job.company_name.charAt(0)}</div>
                </div>
                <div class="job-content">
                    <h3 class="job-title">${job.title}</h3>
                    <p class="job-company">${job.company_name}</p>
                    <div class="job-meta">
                        <span title="Mức lương"><i class="fas fa-money-bill-wave"></i> ${job.salary}</span>
                        <span title="Địa điểm"><i class="fas fa-map-marker-alt"></i> ${job.location}</span>
                        <span title="Hạn nộp"><i class="fas fa-clock"></i> ${formatDateShort(job.deadline)}</span>
                    </div>
                </div>
                <div class="job-action">
                    <i class="fas fa-chevron-right"></i>
                </div>
            `;
            item.addEventListener('click', () => displayJobDetails(job));
            jobListContainer.appendChild(item);
        });
    }

    function displayJobDetails(job) {
        const majorsHtml = job.majors_required
            .split(',')
            .map(major => major.trim() ? `<span class="career-tag">${major.trim()}</span>` : '')
            .join('');

        // Tạo HTML cho nút link gốc, chỉ hiển thị nếu có link
        const sourceLinkHtml = job.source_link 
            ? `<a href="${job.source_link}" class="job-detail-source-link" target="_blank" rel="noopener noreferrer">
                <i class="fas fa-external-link-alt"></i> Xem tin gốc
            </a>`
            : '';

        jobDetailContainer.innerHTML = `
            <div class="job-detail-grid">
                <div class="job-detail-left-column">
                    <h2 class="job-detail-title">${job.title}</h2>
                    <p class="job-detail-company">${job.company_name}</p>
                    
                    ${sourceLinkHtml}
                    
                    <div class="info-card">
                        <p><strong>Mức lương:</strong><span>${job.salary}</span></p>
                        <p><strong>Nơi làm việc:</strong><span>${job.location}</span></p>
                        <p><strong>Hạn nộp:</strong><span>${formatDateShort(job.deadline)}</span></p>
                        <p><strong>Số lượng:</strong><span>${job.positions_available}</span></p>
                    </div>

                    <div class="info-card">
                        <h4>Thông tin tuyển dụng</h4>
                        <p><strong>Kinh nghiệm:</strong><span>${job.experience_required}</span></p>
                        <p><strong>Loại hình:</strong><span>${job.work_type}</span></p>
                        <p><strong>Chuyên ngành:</strong></p>
                        <div class="career-tags">${majorsHtml}</div>
                    </div>
                </div>

                <div class="job-detail-right-column">
                    <div class="job-detail-section">
                        <h3>Mô tả công việc</h3>
                        <div class="detail-content">${job.description || '<p>Không có thông tin.</p>'}</div>
                    </div>
                    <div class="job-detail-section">
                        <h3>Quyền lợi được hưởng</h3>
                        <div class="detail-content">${job.benefits || '<p>Không có thông tin.</p>'}</div>
                    </div>
                    <div class="job-detail-section">
                        <h3>Yêu cầu công việc</h3>
                        <div class="detail-content">${job.requirements || '<p>Không có thông tin.</p>'}</div>
                    </div>
                </div>
            </div>
        `;
        showJobDetailView();
    }

    // Thêm hàm formatDateShort để định dạng ngày ngắn gọn hơn
    function formatDateShort(dateString) {
        if (!dateString || dateString === "Không có hạn nộp") return "N/A";
        try {
            const date = new Date(dateString);
            // Kiểm tra nếu ngày không hợp lệ
            if (isNaN(date.getTime())) {
                return dateString; // Trả về chuỗi gốc nếu không thể parse
            }
            const options = { year: 'numeric', month: '2-digit', day: '2-digit' };
            return date.toLocaleDateString('vi-VN', options);
        } catch (e) {
            console.error("Lỗi định dạng ngày:", e, dateString);
            return dateString;
        }
    }

    function closeJobsModal() {
        jobsModal.classList.add('hidden');
    }

    function showJobDetailView() {
        jobListView.classList.add('hidden');
        jobDetailContainer.classList.remove('hidden');
        jobsModalTitle.textContent = "Chi tiết Việc làm";
        
        if (!document.getElementById('job-back-button')) {
            const backButton = document.createElement('button');
            backButton.id = 'job-back-button';
            backButton.title = 'Quay lại';
            backButton.innerHTML = '<i class="fas fa-arrow-left"></i>';
            backButton.addEventListener('click', showJobListView);
            jobsModalHeader.prepend(backButton);
        }
    }

    function showJobListView() {
        jobListView.classList.remove('hidden');
        jobDetailContainer.classList.add('hidden');
        jobsModalTitle.textContent = "Việc làm & Thực tập";
        const backButton = document.getElementById('job-back-button');
        if (backButton) backButton.remove();
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

    // Job Listeners
    jobsButton.addEventListener('click', openJobsModal);
    closeJobsModalButton.addEventListener('click', closeJobsModal);
    filterJobsButton.addEventListener('click', fetchAndDisplayJobs);

    // Activity Listeners
    activityButton.addEventListener('click', openActivityModal);
    closeActivityModalButton.addEventListener('click', closeActivityModal);

    // Khởi tạo các thành phần ban đầu của trang
    populateFAQs();
});