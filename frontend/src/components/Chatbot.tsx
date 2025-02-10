import React, { useState } from 'react';
import axios from 'axios';
import './Chatbot.css';
import ReactMarkdown from "react-markdown";

const Chatbot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<{ sender: string; text: string }[]>([
    { sender: 'bot', text: 'Welcome to the Nottingham University Chatbot! Feel free to ask a question.' }
  ]);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const toggleChatbot = () => setIsOpen(!isOpen);
  const closeChatbot = () => setIsOpen(false);

  const sendMessage = async () => {
    if (input.trim()) {
      setMessages([...messages, { sender: 'user', text: input }]);
      setIsGenerating(true);
      try{
        const response = await axios.post('http://localhost:8000/chat', { user_query: input });
        setMessages((prevMessages) => [...prevMessages, { sender: 'bot', text: response.data.response }]);
      } catch (error) {
        setMessages((prevMessages) => [...prevMessages, { sender: 'bot', text: 'An error occurred. Please try again.' }]);
      } finally {
        setIsGenerating(false);
      }
      setInput('');
    }
  };

  return (
    <div className="chatbot-container">
      {!isOpen && (  // Hide the speech bubble icon when the chatbot is open
        <div className="chatbot-icon" onClick={toggleChatbot}>
          💬
        </div>
      )}
      {isOpen && (
        <div className="chat-popup">
          <div className="chat-header">
            <span className="chat-title">University Chatbot</span>
            <button className="close-btn" onClick={closeChatbot}>✖</button>
          </div>
          <div className="chat-messages">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.sender}`}>
                <div className="icon">
                  {msg.sender === 'user' ? '👤' : '🤖'}
                </div>
                <div className="text">
                  
                  {msg.sender === 'bot' ? (
                    <ReactMarkdown 
                      components={{
                        a: ({ href, children }) => (
                          <a href={href} target="_blank" rel="noopener noreferrer">
                            {children}
                          </a>
                        )
                      }}>
                        {msg.text}
                        </ReactMarkdown> ): (
                                        msg.text
                                      )}
                  </div>
              </div>
            ))}
            {isGenerating && (
              <div className="message bot">
                <div className="icon">🤖</div>
                <div className="spinner"></div>
              </div>
            )}
          </div>
          <div className="chat-input">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            />
            <button onClick={sendMessage} disabled={isGenerating}>Send</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chatbot;
