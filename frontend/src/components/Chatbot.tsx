import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Chatbot.css';
import ReactMarkdown from "react-markdown";

interface Message {
  sender: string;
  text: string;
}

const Chatbot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'bot', text: 'Welcome to the Nottingham University Chatbot! Feel free to ask a question.' }
  ]);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState("en"); // Default: English

  // State for feature selection mode:
  const [featureSelection, setFeatureSelection] = useState<{ [key: string]: string }>({});
  const [availableFeatures, setAvailableFeatures] = useState<{ [key: string]: string[] } | null>(null);
  const [featureKeys, setFeatureKeys] = useState<string[]>([]);
  const [currentFeatureIndex, setCurrentFeatureIndex] = useState(0);
  const [selectionMode, setSelectionMode] = useState(false);

  useEffect(() => {
    // Generate and store session_id if not already set
    let storedSessionId = sessionStorage.getItem("session_id");
    if (!storedSessionId) {
      storedSessionId = Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem("session_id", storedSessionId);
    }
    setSessionId(storedSessionId);
    console.log("Frontend session_id:", storedSessionId);

    // Load chat history from localStorage (if available)
    const storedMessages = localStorage.getItem(`chat_history_${storedSessionId}`);
    if (storedMessages) {
      setMessages(JSON.parse(storedMessages));
    }
  }, []);

  
  useEffect(() => {
    // Save chat history to localStorage so it persists on refresh
    if (sessionId) {
      localStorage.setItem(`chat_history_${sessionId}`, JSON.stringify(messages));
    }
  }, [messages, sessionId]);

  const toggleChatbot = () => setIsOpen(!isOpen);
  const closeChatbot = () => setIsOpen(false);

   // Function to submit feature selections to backend
  const submitFeatures = async (features: { [key: string]: string }) => {
    setIsGenerating(true);
    try {
      const response = await axios.post('http://localhost:8000/chat', { 
        session_id: sessionId,
        user_query: "course recommendation", 
        user_features: features 
      });
      // Append the recommendation result to the chat
      setMessages((prevMessages) => [...prevMessages, { sender: 'bot', text: response.data.response }]);
    } catch (error) {
      setMessages((prevMessages) => [...prevMessages, { sender: 'bot', text: 'An error occurred while submitting your selections. Please try again.' }]);
    } finally {
      setIsGenerating(false);
      // Exit selection mode
      setSelectionMode(false);
      setAvailableFeatures(null);
      setFeatureSelection({});
      setFeatureKeys([]);
      setCurrentFeatureIndex(0);
    }
  };

  // Handle a feature option click
  const handleFeatureOptionClick = (value: string) => {
    // Get the current feature name from featureKeys array
    const currentFeature = featureKeys[currentFeatureIndex];
    const updatedSelections = { ...featureSelection, [currentFeature]: value };
    setFeatureSelection(updatedSelections);

    // Move to next feature or submit if finished
    if (currentFeatureIndex < featureKeys.length - 1) {
      setCurrentFeatureIndex(currentFeatureIndex + 1);
    } else {
      // All features have been selected; submit to backend
      submitFeatures(updatedSelections);
    }
  };

  // 🌍 Language Selection
  const handleLanguageChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedLanguage(event.target.value);
  };

  const sendMessage = async () => {
    if (input.trim() && !selectionMode) {
      setMessages([...messages, { sender: 'user', text: input }]);
      setIsGenerating(true);
      try{
        const response = await axios.post('http://localhost:8000/chat', { session_id: sessionId, user_query: input , language: selectedLanguage});
      // Check if the response includes feature_selection data
      if (response.data.feature_selection) {
        // Append the prompt message from backend
        setMessages(prev => [...prev, { sender: 'bot', text: response.data.response }]);
        // Set selection mode and store available features
        setAvailableFeatures(response.data.feature_selection);
        const keys = Object.keys(response.data.feature_selection);
        setFeatureKeys(keys);
        setCurrentFeatureIndex(0);
        setSelectionMode(true);
      } else {
        // Normal response without feature selection mode
        setMessages(prev => [...prev, { sender: 'bot', text: response.data.response }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { sender: 'bot', text: 'An error occurred. Please try again.' }]);
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

          <div className="language-select">
            <label>🌍 Language: </label>
            <select value={selectedLanguage} onChange={handleLanguageChange}>
              <option value="en">English</option>
              <option value="zh">Chinese(中文)</option>
            </select>
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
          
          {/* If in feature selection mode, display clickable options */}
          {selectionMode && availableFeatures && featureKeys.length > 0 && (
            <div className="feature-selection">
              <p>
                Select your {featureKeys[currentFeatureIndex]}:
              </p>
              <div className="options">
                {availableFeatures[featureKeys[currentFeatureIndex]].map((option: string, index: number) => (
                  <button key={index} className="option-button" onClick={() => handleFeatureOptionClick(option)}>
                    {option}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Normal chat input only shows when NOT in feature selection mode */}
          {!selectionMode && (
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
          )}
        </div>
      )}
    </div>
  );
};

export default Chatbot;
