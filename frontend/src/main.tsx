import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./i18n";
import "./styles.css";
import { ThemeProvider } from "./context/ThemeContext";
import { ProfilesProvider } from "./context/ProfilesContext";
import { ThreadsProvider } from "./context/ThreadsContext";
import { ToastProvider } from "./components/Toast";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <ProfilesProvider>
          <ThreadsProvider>
            <ToastProvider>
              <App />
            </ToastProvider>
          </ThreadsProvider>
        </ProfilesProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
