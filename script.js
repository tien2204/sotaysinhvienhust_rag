document.getElementById('send-button').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

async function sendMessage() {
    const userInput = document.getElementById('user-input');
    const question = userInput.value.trim();
    if (question === '') {
        return;
    }

    addMessage(question, 'user-message');
    userInput.value = '';

    // Hiển thị animation AI đang "nghĩ"
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

        // Xóa animation khi có câu trả lời
        thinkingMessage.remove();

        // Chuyển đổi Markdown sang HTML và hiển thị
        addMessage(marked.parse(botAnswer), 'bot-message', true);

    } catch (error) {
        console.error('Lỗi:', error);
        if (thinkingMessage) {
            thinkingMessage.remove();
        }
        addMessage('Xin lỗi, đã xảy ra lỗi. Vui lòng thử lại sau.', 'bot-message');
    }
}

function addMessage(text, messageType, isMarkdown = false) {
    const messagesDiv = document.getElementById('messages');
    const messageContainer = document.createElement('div');
    messageContainer.classList.add('message', messageType);

    if (isMarkdown) {
        messageContainer.innerHTML = text;
    } else {
        const messageElement = document.createElement('p');
        messageElement.textContent = text;
        messageContainer.appendChild(messageElement);
    }
    
    messagesDiv.appendChild(messageContainer);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return messageContainer;
}

function addThinkingAnimation() {
    const messagesDiv = document.getElementById('messages');
    const thinkingContainer = document.createElement('div');
    thinkingContainer.classList.add('message', 'bot-message', 'thinking-animation');
    
    // Tạo một icon spinner
    const spinnerIcon = document.createElement('i');
    spinnerIcon.classList.add('fas', 'fa-spinner', 'fa-pulse'); // fa-pulse là class của Font Awesome

    thinkingContainer.appendChild(spinnerIcon);
    messagesDiv.appendChild(thinkingContainer);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return thinkingContainer;
}