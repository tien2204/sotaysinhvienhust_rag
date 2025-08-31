// --- DOM Elements ---
const sendButton = document.getElementById('send-button');
const userInput = document.getElementById('user-input');
const messagesDiv = document.getElementById('messages');
const faqListDiv = document.getElementById('faq-list');

// --- FAQ Data ---
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

// --- Event Listeners ---
sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
// Populate FAQs when the document is loaded
document.addEventListener('DOMContentLoaded', populateFAQs);


// --- Functions ---

/**
 * Sends a user's question to the backend and displays the response.
 */
async function sendMessage() {
    const question = userInput.value.trim();
    if (question === '') {
        return;
    }

    addMessage(question, 'user-message');
    userInput.value = '';

    // Show thinking animation
    const thinkingMessage = addThinkingAnimation();

    try {
        const response = await fetch('http://127.0.0.1:8000/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });

        if (!response.ok) {
            throw new Error('Lỗi khi kết nối đến backend');
        }

        const data = await response.json();
        const botAnswer = data.answer;

        // Remove thinking animation
        thinkingMessage.remove();

        // Convert Markdown to HTML and display the message
        addMessage(marked.parse(botAnswer), 'bot-message', true);

    } catch (error) {
        console.error('Lỗi:', error);
        if (thinkingMessage) {
            thinkingMessage.remove();
        }
        addMessage('Xin lỗi, đã xảy ra lỗi. Vui lòng thử lại sau.', 'bot-message');
    }
}

/**
 * Adds a message to the chat display.
 * @param {string} text - The message content (can be plain text or HTML).
 * @param {string} messageType - The class for the message ('user-message' or 'bot-message').
 * @param {boolean} isHTML - Flag to indicate if the text is HTML.
 * @returns {HTMLElement} The created message container element.
 */
function addMessage(text, messageType, isHTML = false) {
    const messageContainer = document.createElement('div');
    messageContainer.classList.add('message', messageType);

    if (isHTML) {
        messageContainer.innerHTML = text;
    } else {
        const messageElement = document.createElement('p');
        messageElement.textContent = text;
        messageContainer.appendChild(messageElement);
    }
    
    messagesDiv.appendChild(messageContainer);
    // Scroll to the latest message
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return messageContainer;
}

/**
 * Displays a thinking animation in the chat.
 * @returns {HTMLElement} The created animation container element.
 */
function addThinkingAnimation() {
    const thinkingContainer = document.createElement('div');
    thinkingContainer.classList.add('message', 'bot-message', 'thinking-animation');
    
    const spinnerIcon = document.createElement('i');
    spinnerIcon.classList.add('fas', 'fa-spinner', 'fa-pulse');

    thinkingContainer.appendChild(spinnerIcon);
    messagesDiv.appendChild(thinkingContainer);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return thinkingContainer;
}

/**
 * Populates the FAQ section with clickable questions.
 */
function populateFAQs() {
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
