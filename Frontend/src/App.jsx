import { useEffect, useRef, useState } from "react";
import API from "./api";
import "./App.css";

// ============================================================
// HELPERS
// ============================================================

const formatCellValue = (value) => {
  if (value === null || value === undefined) return "—";

  if (typeof value === "number") {
    if (!Number.isFinite(value)) return "—";

    return Number.isInteger(value)
      ? value.toLocaleString()
      : value.toLocaleString(undefined, {
          maximumFractionDigits: 2,
        });
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return "[Object]";
    }
  }

  return String(value);
};

const normalizeRow = (row) => {
  if (row === null || row === undefined) return {};

  if (
    typeof row === "object" &&
    !Array.isArray(row)
  ) {
    return row;
  }

  return {
    value: row,
  };
};

const getColumns = (rows) => {
  const columns = new Set();

  if (!Array.isArray(rows)) {
    return [];
  }

  rows.forEach((row) => {
    if (
      row &&
      typeof row === "object" &&
      !Array.isArray(row)
    ) {
      Object.keys(row).forEach((column) => {
        columns.add(column);
      });
    }
  });

  return Array.from(columns);
};

const normalizeResult = (result) => {
  if (result === null || result === undefined) {
    return {
      columns: [],
      rows: [],
      scalar: null,
    };
  }

  if (typeof result !== "object") {
    return {
      columns: ["value"],
      rows: [{ value: result }],
      scalar: result,
    };
  }

  if (Array.isArray(result)) {
    if (result.length === 0) {
      return {
        columns: [],
        rows: [],
        scalar: null,
      };
    }

    // Array of objects
    if (
      typeof result[0] === "object" &&
      result[0] !== null &&
      !Array.isArray(result[0])
    ) {
      const rows = result.map(normalizeRow);

      return {
        columns: getColumns(rows),
        rows,
        scalar: null,
      };
    }

    // Array of scalar values
    if (!Array.isArray(result[0])) {
      const rows = result.map((value) => ({
        value,
      }));

      return {
        columns: ["value"],
        rows,
        scalar: null,
      };
    }

    // Array of arrays
    const rows = result.map((row) => {
      const record = {};

      row.forEach((value, index) => {
        record[`column_${index + 1}`] = value;
      });

      return record;
    });

    return {
      columns:
        rows.length > 0
          ? Object.keys(rows[0])
          : [],
      rows,
      scalar: null,
    };
  }

  // Backend response:
  // {
  //   columns: [],
  //   rows: [],
  //   row_count: number
  // }
  if (
    typeof result === "object" &&
    Array.isArray(result.rows)
  ) {
    let rows = result.rows;

    // Convert array rows to objects
    if (
      rows.length > 0 &&
      Array.isArray(rows[0])
    ) {
      const backendColumns =
        Array.isArray(result.columns)
          ? result.columns
          : [];

      rows = rows.map((row) => {
        const record = {};

        row.forEach((value, index) => {
          const column =
            backendColumns[index] ||
            `column_${index + 1}`;

          record[column] = value;
        });

        return record;
      });
    }

    rows = rows.map(normalizeRow);

    const columns =
      Array.isArray(result.columns) &&
      result.columns.length > 0
        ? result.columns
        : getColumns(rows);

    return {
      columns,
      rows,
      scalar: null,
      rowCount:
        result.row_count ?? rows.length,
    };
  }

  return {
    columns: Object.keys(result),
    rows: [result],
    scalar: null,
  };
};

// ============================================================
// APP
// ============================================================

function App() {
  const fileInputRef = useRef(null);

  // ==========================================================
  // STATE
  // ==========================================================

  const [file, setFile] = useState(null);
  const [dataset, setDataset] = useState(null);

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);

  const [error, setError] = useState("");
  const [dragActive, setDragActive] = useState(false);

  const [theme, setTheme] = useState(
    localStorage.getItem("queryra-theme") || "dark"
  );

  const [sidebarOpen, setSidebarOpen] =
    useState(false);

  const [history, setHistory] = useState([]);

  // ==========================================================
  // THEME
  // ==========================================================

  useEffect(() => {
    document.documentElement.dataset.theme =
      theme;

    localStorage.setItem(
      "queryra-theme",
      theme
    );
  }, [theme]);

  // ==========================================================
  // FILE SELECTION
  // ==========================================================

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return;

    const allowedExtensions = [
      ".csv",
      ".xlsx",
      ".xls",
    ];

    const fileName =
      selectedFile.name.toLowerCase();

    const isValid =
      allowedExtensions.some((extension) =>
        fileName.endsWith(extension)
      );

    if (!isValid) {
      setError(
        "Please upload a CSV or Excel file."
      );
      return;
    }

    setFile(selectedFile);
    setDataset(null);
    setAnswer(null);
    setQuestion("");
    setError("");
  };

  // ==========================================================
  // DRAG & DROP
  // ==========================================================

  const handleDragOver = (event) => {
    event.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setDragActive(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragActive(false);

    const droppedFile =
      event.dataTransfer.files?.[0];

    handleFileSelect(droppedFile);
  };

  // ==========================================================
  // PREVIEW
  // ==========================================================

  const loadPreview = async (datasetId) => {
    try {
      const response =
        await API.get(
          `/datasets/${datasetId}/preview`
        );

      setDataset((previous) => ({
        ...previous,
        preview:
          Array.isArray(
            response.data?.preview
          )
            ? response.data.preview
            : [],
      }));
    } catch (err) {
      console.error(
        "Preview error:",
        err
      );

      setError(
        "Dataset uploaded, but preview could not be loaded."
      );
    }
  };

  // ==========================================================
  // UPLOAD
  // ==========================================================

  const handleUpload = async () => {
    if (!file) {
      setError(
        "Please select a CSV or Excel file first."
      );
      return;
    }

    setUploading(true);
    setError("");
    setAnswer(null);

    try {
      const formData = new FormData();

      formData.append(
        "file",
        file
      );

      const response =
        await API.post(
          "/upload-data",
          formData,
          {
            headers: {
              "Content-Type":
                "multipart/form-data",
            },
          }
        );

      setDataset(response.data);

      if (response.data?.dataset_id) {
        await loadPreview(
          response.data.dataset_id
        );
      }

      setSidebarOpen(false);
    } catch (err) {
      console.error(
        "Upload error:",
        err
      );

      setError(
        err.response?.data?.detail?.error ||
          err.response?.data?.detail?.message ||
          err.response?.data?.detail ||
          "Dataset upload failed."
      );
    } finally {
      setUploading(false);
    }
  };

  // ==========================================================
  // ASK QUERYRA AI
  // ==========================================================

  const handleAsk = async () => {
    if (!dataset?.dataset_id) {
      setError(
        "Please upload a dataset first."
      );
      return;
    }

    if (!question.trim()) {
      setError(
        "Please enter a question."
      );
      return;
    }

    setAsking(true);
    setError("");

    try {
      const currentQuestion =
        question.trim();

      const payload = {
        dataset_id:
          dataset.dataset_id,
        question:
          currentQuestion,
      };

      const response =
        await API.post(
          "/ask",
          payload
        );

      const result =
        response.data;

      setAnswer(result);

      setHistory((previous) => [
        {
          id:
            result.query_history_id ||
            Date.now(),

          question:
            currentQuestion,

          time:
            new Date().toLocaleTimeString(
              [],
              {
                hour: "2-digit",
                minute: "2-digit",
              }
            ),
        },
        ...previous,
      ]);

      setQuestion("");

      // Scroll to result
      setTimeout(() => {
        document
          .getElementById(
            "results-section"
          )
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      }, 100);
    } catch (err) {
      console.error(
        "QUERYRA ASK ERROR:",
        err
      );

      if (
        err.code ===
        "ECONNABORTED"
      ) {
        setError(
          "The Queryra AI request timed out. Please check your backend connection."
        );
      } else if (
        err.response
      ) {
        setError(
          err.response.data?.detail?.error ||
            err.response.data?.detail?.message ||
            err.response.data?.detail ||
            "Backend failed to process the question."
        );
      } else if (err.request) {
        setError(
          "No response received from the Queryra backend."
        );
      } else {
        setError(
          err.message ||
            "Failed to process your question."
        );
      }
    } finally {
      setAsking(false);
    }
  };

  // ==========================================================
  // CLEAR DATASET
  // ==========================================================

  const handleClear = () => {
    setFile(null);
    setDataset(null);
    setAnswer(null);
    setQuestion("");
    setError("");
    setHistory([]);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  // ==========================================================
  // COPY SQL
  // ==========================================================

  const copySQL = async () => {
    if (!answer?.sql) return;

    try {
      await navigator.clipboard.writeText(
        answer.sql
      );
    } catch (err) {
      console.error(
        "Copy SQL failed:",
        err
      );
    }
  };

  // ==========================================================
  // PREVIEW DATA
  // ==========================================================

  const previewRows =
    Array.isArray(dataset?.preview)
      ? dataset.preview.map(
          normalizeRow
        )
      : [];

  const previewColumns =
    getColumns(previewRows);

  // ==========================================================
  // RESULT DATA
  // ==========================================================

  const normalizedResult =
    normalizeResult(
      answer?.result
    );

  const resultRows =
    normalizedResult.rows;

  const resultColumns =
    normalizedResult.columns;

  // ==========================================================
  // DATASET INFO
  // ==========================================================

  const datasetInfo =
    dataset?.dataset || {};

  const datasetName =
    datasetInfo.filename ||
    file?.name ||
    "No dataset";

  // ==========================================================
  // UI
  // ==========================================================

  return (
    <div className="app-shell">

      {/* ====================================================
          MOBILE OVERLAY
      ==================================================== */}

      {sidebarOpen && (
        <div
          className="mobile-overlay"
          onClick={() =>
            setSidebarOpen(false)
          }
        />
      )}

      {/* ====================================================
          LEFT SIDEBAR
      ==================================================== */}

      <aside
        className={`sidebar ${
          sidebarOpen
            ? "sidebar-open"
            : ""
        }`}
      >

        {/* BRAND */}

        <div className="sidebar-brand">

          <div className="brand-bot">
            Q
          </div>

          <div>
            <strong>
              Queryra
            </strong>

            <span>
              AI Data Intelligence
            </span>
          </div>

        </div>

        {/* BRAND LABEL */}

        <div
          style={{
            padding:
              "0 8px 12px",
          }}
        >
          <span
            style={{
              fontSize: "7px",
              color:
                "var(--muted)",
              letterSpacing:
                "0.12em",
            }}
          >
            INTELLIGENT DATA ANALYSIS
          </span>
        </div>

        {/* NAVIGATION */}

        <nav className="main-nav">

          <button
            className="nav-item active"
            onClick={() => {
              window.scrollTo({
                top: 0,
                behavior:
                  "smooth",
              });

              setSidebarOpen(false);
            }}
          >
            <span className="nav-icon">
              ⌂
            </span>

            Dashboard
          </button>

          <button
            className="nav-item"
            onClick={() => {
              document
                .getElementById(
                  "ask-section"
                )
                ?.scrollIntoView({
                  behavior:
                    "smooth",
                });

              setSidebarOpen(false);
            }}
          >
            <span className="nav-icon">
              ✦
            </span>

            Ask Queryra
          </button>

          <button
            className="nav-item"
            onClick={() => {
              document
                .getElementById(
                  "results-section"
                )
                ?.scrollIntoView({
                  behavior:
                    "smooth",
                });

              setSidebarOpen(false);
            }}
          >
            <span className="nav-icon">
              ▤
            </span>

            Results
          </button>

        </nav>

        {/* USER / PRODUCT CARD */}

        <div className="sidebar-user">

          <div className="avatar">
            Q
          </div>

          <div className="user-info">

            <strong>
              Queryra User
            </strong>

            <span>
              AI Data Intelligence
            </span>

          </div>

          <span className="user-arrow">
            ›
          </span>

        </div>

      </aside>

      {/* ====================================================
          MAIN AREA
      ==================================================== */}

      <div className="main-area">

        {/* ==================================================
            TOPBAR
        ================================================== */}

        <header className="topbar">

          <button
            className="mobile-menu"
            onClick={() =>
              setSidebarOpen(
                !sidebarOpen
              )
            }
            aria-label="Open menu"
          >
            ☰
          </button>

          <span className="mobile-title">
            Queryra
          </span>

          <div className="topbar-actions">

            {/* THEME */}

            <button
              className="theme-toggle"
              onClick={() =>
                setTheme(
                  theme === "dark"
                    ? "light"
                    : "dark"
                )
              }
              aria-label="Toggle theme"
            >

              <span>
                {theme === "dark"
                  ? "☾"
                  : "☀"}
              </span>

              {theme === "dark"
                ? "Dark"
                : "Light"}

            </button>

            {/* USER */}

            <div className="top-user">

              <div className="avatar small">
                Q
              </div>

              <span>
                Queryra
              </span>

            </div>

          </div>

        </header>

        {/* ==================================================
            WORKSPACE
        ================================================== */}

        <main className="workspace">

          {/* =================================================
              CENTER
          ================================================= */}

          <section className="center-panel">

            {/* =================================================
                HERO
            ================================================= */}

            <div className="assistant-header">

              <div className="assistant-logo">
                Q
              </div>

              <div>

                <h1>
                  Queryra
                </h1>

                <p>
                  Turn your data into
                  answers with AI-powered
                  data intelligence.
                </p>

              </div>

            </div>

            {/* =================================================
                FEATURES
            ================================================= */}

            {!dataset && (
              <div className="feature-grid">

                <div className="feature-card">

                  <div className="feature-icon green">
                    ↗
                  </div>

                  <div>

                    <strong>
                      Ask Naturally
                    </strong>

                    <span>
                      Ask questions about
                      your dataset in plain
                      English.
                    </span>

                  </div>

                </div>

                <div className="feature-card">

                  <div className="feature-icon yellow">
                    ◈
                  </div>

                  <div>

                    <strong>
                      Smart SQL
                    </strong>

                    <span>
                      Queryra converts your
                      questions into SQL
                      automatically.
                    </span>

                  </div>

                </div>

                <div className="feature-card">

                  <div className="feature-icon purple">
                    ◫
                  </div>

                  <div>

                    <strong>
                      Instant Insights
                    </strong>

                    <span>
                      Analyze your data and
                      receive results instantly.
                    </span>

                  </div>

                </div>

              </div>
            )}

            {/* =================================================
                UPLOAD
            ================================================= */}

            {!dataset && (
              <section
                className="upload-workspace"
                onDragOver={
                  handleDragOver
                }
                onDragLeave={
                  handleDragLeave
                }
                onDrop={
                  handleDrop
                }
                style={
                  dragActive
                    ? {
                        borderColor:
                          "var(--primary-light)",
                        background:
                          "rgba(245, 184, 56, 0.06)",
                      }
                    : {}
                }
              >

                <div className="upload-workspace-icon">
                  ↑
                </div>

                <h2>
                  Start with your data
                </h2>

                <p>
                  Upload a CSV or Excel
                  dataset and let Queryra
                  help you explore, query
                  and understand it.
                </p>

                <button
                  className="primary-button"
                  onClick={() =>
                    fileInputRef.current?.click()
                  }
                >
                  Choose Dataset →
                </button>

                <input
                  ref={
                    fileInputRef
                  }
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  hidden
                  onChange={(
                    event
                  ) =>
                    handleFileSelect(
                      event.target
                        .files?.[0]
                    )
                  }
                />

                {file && (
                  <div className="selected-file">

                    <strong>
                      {file.name}
                    </strong>

                    <button
                      className="primary-button small"
                      onClick={
                        handleUpload
                      }
                      disabled={
                        uploading
                      }
                    >
                      {uploading
                        ? "Analyzing..."
                        : "Upload"}
                    </button>

                  </div>
                )}

              </section>
            )}

            {/* =================================================
                ACTIVE DATASET
            ================================================= */}

            {dataset && (
              <>

                {/* =================================================
                    DATASET READY
                ================================================= */}

                <div className="conversation">

                  {question && (
                    <div className="message user-message">

                      <span className="message-label">
                        YOUR QUESTION
                      </span>

                      <div className="message-bubble">
                        {question}
                      </div>

                    </div>
                  )}

                  <div className="message">

                    <div className="ai-message-header">

                      <div className="mini-ai">
                        Q
                      </div>

                      <span>
                        Queryra AI
                      </span>

                    </div>

                    <p className="ai-intro">
                      Your dataset is ready.
                      Ask Queryra anything
                      about your data.
                    </p>

                  </div>

                </div>

                {/* =================================================
                    DATA PREVIEW
                ================================================= */}

                <section className="results-card">

                  <div className="results-header">

                    <div>

                      <span>
                        ACTIVE DATASET
                      </span>

                      <h2>
                        {datasetName}
                      </h2>

                    </div>

                    <button
                      className="copy-result"
                      onClick={
                        handleClear
                      }
                    >
                      × Change
                    </button>

                  </div>

                  {previewRows.length >
                  0 ? (

                    <div className="result-table-wrapper">

                      <table>

                        <thead>

                          <tr>

                            {previewColumns.map(
                              (
                                column
                              ) => (
                                <th
                                  key={
                                    column
                                  }
                                >
                                  {
                                    column
                                  }
                                </th>
                              )
                            )}

                          </tr>

                        </thead>

                        <tbody>

                          {previewRows.map(
                            (
                              row,
                              index
                            ) => (
                              <tr
                                key={
                                  index
                                }
                              >

                                {previewColumns.map(
                                  (
                                    column
                                  ) => (
                                    <td
                                      key={
                                        column
                                      }
                                    >
                                      {formatCellValue(
                                        row[
                                          column
                                        ]
                                      )}
                                    </td>
                                  )
                                )}

                              </tr>
                            )
                          )}

                        </tbody>

                      </table>

                    </div>

                  ) : (

                    <div className="empty-result">
                      No preview data available.
                    </div>

                  )}

                </section>

                {/* =================================================
                    ASK QUERYRA
                ================================================= */}

                <section
                  id="ask-section"
                  className="ask-section"
                >

                  <div className="assistant-header">

                    <div className="assistant-logo">
                      Q
                    </div>

                    <div>

                      <h1>
                        Ask Queryra
                      </h1>

                      <p>
                        What would you like
                        to discover?
                      </p>

                    </div>

                  </div>

                  <div className="question-input">

                    <textarea
                      value={
                        question
                      }
                      onChange={(
                        event
                      ) =>
                        setQuestion(
                          event.target
                            .value
                        )
                      }
                      onKeyDown={(
                        event
                      ) => {

                        if (
                          event.key ===
                            "Enter" &&
                          !event.shiftKey
                        ) {
                          event.preventDefault();
                          handleAsk();
                        }

                      }}
                      placeholder="Ask something like: What are the total sales by city?"
                      rows={2}
                      disabled={
                        asking
                      }
                    />

                    <button
                      className="send-button"
                      onClick={
                        handleAsk
                      }
                      disabled={
                        asking ||
                        !question.trim()
                      }
                      aria-label="Ask Queryra"
                    >
                      {asking
                        ? "..."
                        : "↑"}
                    </button>

                  </div>

                </section>

                {/* =================================================
                    LOADING
                ================================================= */}

                {asking && (
                  <div className="message">

                    <div className="ai-message-header">

                      <div className="mini-ai">
                        Q
                      </div>

                      <span>
                        Queryra is analyzing...
                      </span>

                    </div>

                    <div className="typing-indicator">
                      <span />
                      <span />
                      <span />
                    </div>

                  </div>
                )}

                {/* =================================================
                    AI RESULT
                ================================================= */}

                {answer && (
                  <section
                    id="results-section"
                    className="results-card"
                  >

                    {/* RESULT HEADER */}

                    <div className="results-header">

                      <div>

                        <span>
                          QUERYRA RESPONSE
                        </span>

                        <h2>
                          Analysis Result
                        </h2>

                      </div>

                    </div>

                    {/* QUESTION */}

                    <div className="message">

                      <span className="message-label">
                        YOUR QUESTION
                      </span>

                      <div className="message-bubble">
                        {formatCellValue(
                          answer.question
                        )}
                      </div>

                    </div>

                    {/* INSIGHT */}

                    <div className="insight-card">

                      <div className="insight-icon">
                        ✦
                      </div>

                      <div>

                        <span>
                          QUERYRA INSIGHT
                        </span>

                        <p>
                          Queryra generated
                          and executed a SQL
                          query against your
                          dataset successfully.
                        </p>

                      </div>

                    </div>

                    {/* =================================================
                        GENERATED SQL
                    ================================================= */}

                    {answer.sql && (
                      <div className="sql-card">

                        <div className="sql-header">

                          <div>

                            <strong>
                              Generated SQL
                            </strong>

                            <span>
                              QUERY
                            </span>

                          </div>

                          <button
                            onClick={
                              copySQL
                            }
                            title="Copy SQL"
                            aria-label="Copy SQL"
                          >
                            ⧉
                          </button>

                        </div>

                        <pre>
                          {answer.sql}
                        </pre>

                        <div className="sql-footer">

                          <span>
                            Generated by Queryra AI
                          </span>

                          <div className="helpful">

                            <span>
                              Helpful?
                            </span>

                            <button
                              type="button"
                              aria-label="Helpful"
                            >
                              👍
                            </button>

                            <button
                              type="button"
                              aria-label="Not helpful"
                            >
                              👎
                            </button>

                          </div>

                        </div>

                      </div>
                    )}

                    {/* =================================================
                        QUERY RESULT
                    ================================================= */}

                    <div className="results-card">

                      <div className="results-header">

                        <div>

                          <span>
                            QUERY RESULT
                          </span>

                          <h2>
                            Data
                          </h2>

                        </div>

                        {resultRows.length >
                          0 && (
                          <span>
                            {resultRows.length}{" "}
                            rows
                          </span>
                        )}

                      </div>

                      {resultRows.length >
                      0 ? (

                        <div className="result-table-wrapper">

                          <table>

                            <thead>

                              <tr>

                                {resultColumns.map(
                                  (
                                    column
                                  ) => (
                                    <th
                                      key={
                                        column
                                      }
                                    >
                                      {
                                        column
                                      }
                                    </th>
                                  )
                                )}

                              </tr>

                            </thead>

                            <tbody>

                              {resultRows.map(
                                (
                                  row,
                                  rowIndex
                                ) => (
                                  <tr
                                    key={
                                      rowIndex
                                    }
                                  >

                                    {resultColumns.map(
                                      (
                                        column
                                      ) => (
                                        <td
                                          key={
                                            column
                                          }
                                        >
                                          {formatCellValue(
                                            row[
                                              column
                                            ]
                                          )}
                                        </td>
                                      )
                                    )}

                                  </tr>
                                )
                              )}

                            </tbody>

                          </table>

                        </div>

                      ) : (

                        <pre className="empty-result">
                          {JSON.stringify(
                            answer.result,
                            null,
                            2
                          )}
                        </pre>

                      )}

                    </div>

                  </section>
                )}

              </>
            )}

          </section>

          {/* =================================================
              RIGHT SIDEBAR
          ================================================= */}

          <aside className="right-sidebar">

            {/* =================================================
                SYSTEM STATUS
            ================================================= */}

            <div className="right-card">

              <div className="right-card-title">

                <span className="online-dot" />

                Queryra Status

              </div>

              <div className="active-dataset">

                <span className="dataset-dot" />

                <strong>
                  Queryra AI Online
                </strong>

              </div>

            </div>

            {/* =================================================
                ACTIVE DATASET
            ================================================= */}

            <div className="right-card">

              <div className="right-card-title">
                Active Dataset
              </div>

              {dataset ? (

                <>

                  <div className="active-dataset">

                    <span className="dataset-dot" />

                    <strong>
                      {datasetName}
                    </strong>

                  </div>

                  <div className="dataset-meta">

                    <span>
                      {datasetInfo.rows ??
                        "—"}{" "}
                      rows
                    </span>

                    <span>
                      •
                    </span>

                    <span>
                      {datasetInfo.columns ??
                        "—"}{" "}
                      columns
                    </span>

                  </div>

                  <button
                    className="change-dataset"
                    onClick={
                      handleClear
                    }
                  >
                    Change Dataset
                  </button>

                </>

              ) : (

                <div className="no-dataset">
                  Upload a dataset to
                  begin analysis.
                </div>

              )}

            </div>

            {/* =================================================
                SCHEMA
            ================================================= */}

            {dataset && (
              <div className="right-card">

                <div className="right-card-title">
                  Dataset Schema
                </div>

                <div className="schema-list">

                  {previewColumns
                    .slice(0, 8)
                    .map(
                      (
                        column
                      ) => {

                        const sample =
                          previewRows.find(
                            (
                              row
                            ) =>
                              row[
                                column
                              ] !==
                                null &&
                              row[
                                column
                              ] !==
                                undefined
                          )?.[
                            column
                          ];

                        let type =
                          "text";

                        if (
                          typeof sample ===
                          "number"
                        ) {
                          type =
                            "number";
                        } else if (
                          typeof sample ===
                          "boolean"
                        ) {
                          type =
                            "boolean";
                        }

                        return (
                          <div
                            className="schema-item"
                            key={
                              column
                            }
                          >

                            <span className="schema-icon">
                              #
                            </span>

                            <span className="schema-name">
                              {
                                column
                              }
                            </span>

                            <span className="schema-type">
                              {
                                type
                              }
                            </span>

                          </div>
                        );
                      }
                    )}

                </div>

              </div>
            )}

            {/* =================================================
                HISTORY
            ================================================= */}

            <div className="right-card">

              <div className="right-card-title">
                Recent Queries
              </div>

              {history.length >
              0 ? (

                <div className="history-list">

                  {history
                    .slice(0, 5)
                    .map(
                      (
                        item
                      ) => (

                        <button
                          className="history-item"
                          key={
                            item.id
                          }
                          onClick={() =>
                            setQuestion(
                              item.question
                            )
                          }
                        >

                          <span className="history-question">
                            {
                              item.question
                            }
                          </span>

                          <span className="history-time">
                            {
                              item.time
                            }
                          </span>

                        </button>

                      )
                    )}

                </div>

              ) : (

                <div className="no-dataset">
                  Your recent questions
                  will appear here.
                </div>

              )}

            </div>

          </aside>

        </main>

        {/* ==================================================
            ERROR
        ================================================== */}

        {error && (
          <div
            className="error-message"
            style={{
              position:
                "fixed",
              bottom: "20px",
              right: "20px",
              zIndex: 200,
              maxWidth:
                "420px",
            }}
          >

            <span>
              !
            </span>

            {error}

          </div>
        )}

      </div>

    </div>
  );
}

export default App;