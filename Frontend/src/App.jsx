import { useEffect, useState } from "react";
import api from "./services/api";

function App() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    async function fetchHealth() {
      try {
        const response = await api.get("/health");
        setHealth(response.data);
      } catch (error) {
        console.error(error);
      }
    }

    fetchHealth();
  }, []);

  return (
    <div style={{ padding: "40px" }}>
      <h1>AI SQL Assistant</h1>

      {health ? (
        <>
          <h2>Backend Status</h2>
          <p>Status: {health.status}</p>
          <p>Message: {health.message}</p>
        </>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}

export default App;