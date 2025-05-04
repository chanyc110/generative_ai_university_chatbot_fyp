import React from 'react';
import Chatbot from './components/Chatbot';

const App: React.FC = () => {
  return (
    <div
      className="App"
      style={{
        backgroundImage: "url('/UNM-Trent-Building.jpg')",
        backgroundSize: "cover",
        backgroundRepeat: "no-repeat",
        backgroundPosition: "center",
        minHeight: "100vh",
      }}
    >
      <h1 style={{ color: "white" }}>University of Nottingham Malaysia</h1>
      <Chatbot />
    </div>
  );
};

export default App;

