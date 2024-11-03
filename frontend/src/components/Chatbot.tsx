import React, { useState } from 'react';
import axios from 'axios';
import './Chatbot.css';

const Chatbot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<{ sender: string; text: string }[]>([]);
  const [input, setInput] = useState('');

  const toggleChatbot = () => setIsOpen(!isOpen);

  const sendMessage = async () => {
    if (input.trim()) {
      setMessages([...messages, { sender: 'user', text: input }]);
      const response = await axios.post('http://localhost:8000/chat', { user_query: input });
      setMessages((prevMessages) => [...prevMessages, { sender: 'bot', text: response.data.response }]);
      setInput('');
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-icon" onClick={toggleChatbot}>
        💬
      </div>
      {isOpen && (
        <div className="chat-popup">
          <div className="chat-header">University Chatbot</div>
          <div className="chat-messages">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.sender}`}>
                <div className="icon">
                  {msg.sender === 'user' ? '👤' : '🤖'}
                </div>
                <div className="text">{msg.text}</div>
              </div>
            ))}
          </div>
          <div className="chat-input">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            />
            <button onClick={sendMessage}>Send</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chatbot;
