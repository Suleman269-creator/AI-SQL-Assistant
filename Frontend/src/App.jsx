import { useRef, useState } from "react";
import API from "./api";
import "./App.css";

// ============================================================
// SAFE VALUE FORMATTER
// ============================================================

const formatCellValue = (value) => {
  if (value === null || value === undefined) {
    return "—";
  }

  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      return "—";
    }

    return Number.isInteger(value)
      ? value.toLocaleString()
      : value.toLocaleString(undefined, {
          maximumFractionDigits: 2,
        });
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (value instanceof Date) {
    return value.toLocaleDateString();
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

// ============================================================
// NORMALIZE ROW
// ============================================================

const normalizeRow = (row) => {
  if (row === null || row === undefined) {
    return {};
  }

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

// ============================================================
// GET COLUMNS
// ============================================================

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

// ============================================================
// NORMALIZE AI RESULT
// ============================================================

const normalizeResult = (result) => {
  if (
    result === null ||
    result === undefined
  ) {
    return {
      columns: [],
      rows: [],
      scalar: null,
      rowCount: 0,
    };
  }

  // Scalar
  if (typeof result !== "object") {
    return {
      columns: ["value"],
      rows: [
        {
          value: result,
        },
      ],
      scalar: result,
      rowCount: 1,
    };
  }

  // Array
  if (Array.isArray(result)) {
    if (result.length === 0) {
      return {
        columns: [],
        rows: [],
        scalar: null,
        rowCount: 0,
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
        rowCount: rows.length,
      };
    }

    // Array of primitive values
    if (!Array.isArray(result[0])) {
      const rows = result.map((value) => ({
        value,
      }));

      return {
        columns: ["value"],
        rows,
        scalar: null,
        rowCount: rows.length,
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
      rowCount: rows.length,
    };
  }

  // Backend result
  if (Array.isArray(result.rows)) {
    let rows = result.rows;

    // Rows as arrays
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
        result.row_count ??
        rows.length,
    };
  }

  // Single object
  return {
    columns: Object.keys(result),
    rows: [result],
    scalar: null,
    rowCount: 1,
  };
};

// ============================================================
// DETECT PRIMARY RESULT
// ============================================================

const getPrimaryResult = (
  columns,
  rows
) => {
  if (
    !Array.isArray(columns) ||
    !Array.isArray(rows) ||
    rows.length === 0
  ) {
    return null;
  }

  const firstRow = rows[0];

  if (!firstRow) {
    return null;
  }

  // Prefer common aggregate columns
  const preferredColumn =
    columns.find((column) => {
      const normalized =
        String(column).toLowerCase();

      return (
        normalized.includes("total") ||
        normalized.includes("sum") ||
        normalized.includes("count") ||
        normalized.includes("average") ||
        normalized.includes("avg") ||
        normalized.includes("sales") ||
        normalized.includes("revenue")
      );
    }) || columns[0];

  return {
    column: preferredColumn,
    value:
      firstRow[preferredColumn],
  };
};

// ============================================================
// FORMAT COLUMN NAME
// ============================================================

const formatColumnName = (column) => {
  if (!column) {
    return "";
  }

  return String(column)
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim();
};

// ============================================================
// APP
// ============================================================

function App() {
  const fileInputRef = useRef(null);

  // ==========================================================
  // STATE
  // ==========================================================

  const [file, setFile] =
    useState(null);

  const [uploading, setUploading] =
    useState(false);

  const [dataset, setDataset] =
    useState(null);

  const [question, setQuestion] =
    useState("");

  const [asking, setAsking] =
    useState(false);

  const [answer, setAnswer] =
    useState(null);

  const [error, setError] =
    useState("");

  const [dragActive, setDragActive] =
    useState(false);

  // ==========================================================
  // FILE SELECTION
  // ==========================================================

  const handleFileSelect = (
    selectedFile
  ) => {
    if (!selectedFile) {
      return;
    }

    const allowedExtensions = [
      ".csv",
      ".xlsx",
      ".xls",
    ];

    const fileName =
      selectedFile.name.toLowerCase();

    const isValid =
      allowedExtensions.some(
        (extension) =>
          fileName.endsWith(extension)
      );

    if (!isValid) {
      setError(
        "Please upload a CSV or Excel file."
      );

      return;
    }

    setFile(selectedFile);
    setError("");
    setAnswer(null);
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
  // LOAD PREVIEW
  // ==========================================================

  const loadPreview = async (
    datasetId
  ) => {
    try {
      const response =
        await API.get(
          `/datasets/${datasetId}/preview`
        );

      console.log(
        "Dataset preview:",
        response.data
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
    } catch (previewError) {
      console.error(
        "Preview error:",
        previewError
      );

      setError(
        "Dataset uploaded, but preview could not be loaded."
      );
    }
  };

  // ==========================================================
  // UPLOAD DATASET
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
      const formData =
        new FormData();

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

      console.log(
        "Upload response:",
        response.data
      );

      setDataset(
        response.data
      );

      await loadPreview(
        response.data.dataset_id
      );
    } catch (uploadError) {
      console.error(
        "Upload error:",
        uploadError
      );

      const detail =
        uploadError.response?.data
          ?.detail;

      setError(
        detail?.error ||
          detail?.message ||
          detail ||
          "Dataset upload failed."
      );
    } finally {
      setUploading(false);
    }
  };

  // ==========================================================
  // ASK AI
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
    setAnswer(null);

    try {
      const payload = {
        dataset_id:
          dataset.dataset_id,

        question:
          question.trim(),
      };

      console.log(
        "Sending /ask request:",
        payload
      );

      const response =
        await API.post(
          "/ask",
          payload
        );

      console.log(
        "AI response:",
        response.data
      );

      setAnswer(
        response.data
      );
    } catch (askError) {
      console.error(
        "ASK ERROR:",
        askError
      );

      if (
        askError.code ===
        "ECONNABORTED"
      ) {
        setError(
          "The AI request timed out. Please check the backend or Gemini API."
        );
      } else if (
        askError.response
      ) {
        const status =
          askError.response.status;

        const detail =
          askError.response.data
            ?.detail;

        console.error(
          "Backend response:",
          askError.response.data
        );

        // ====================================================
        // GEMINI QUOTA ERROR
        // ====================================================

        if (
          status === 429 ||
          String(
            detail?.error || ""
          )
            .toLowerCase()
            .includes("quota") ||
          String(
            detail?.message || ""
          )
            .toLowerCase()
            .includes("quota")
        ) {
          setError(
            `${detail?.message || "Gemini API quota has been exceeded."} ${
              detail?.suggestion || ""
            }`.trim()
          );
        }

        // ====================================================
        // SQL ERROR
        // ====================================================

        else if (
          status === 400
        ) {
          setError(
            detail?.error ||
              detail?.message ||
              "The generated SQL could not be executed."
          );
        }

        // ====================================================
        // DATASET ERROR
        // ====================================================

        else if (
          status === 404
        ) {
          setError(
            detail?.message ||
              detail ||
              "Dataset was not found."
          );
        }

        // ====================================================
        // GENERAL BACKEND ERROR
        // ====================================================

        else {
          setError(
            detail?.error ||
              detail?.message ||
              detail ||
              "Backend failed to process the question."
          );
        }
      } else if (
        askError.request
      ) {
        setError(
          "No response received from backend. Make sure FastAPI is running."
        );
      } else {
        setError(
          askError.message ||
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

    if (
      fileInputRef.current
    ) {
      fileInputRef.current.value =
        "";
    }
  };

  // ==========================================================
  // PREVIEW DATA
  // ==========================================================

  const previewRows =
    Array.isArray(
      dataset?.preview
    )
      ? dataset.preview.map(
          normalizeRow
        )
      : [];

  const previewColumns =
    getColumns(previewRows);

  // ==========================================================
  // AI RESULT
  // ==========================================================

  const normalizedResult =
    normalizeResult(
      answer?.result
    );

  const resultRows =
    normalizedResult.rows;

  const resultColumns =
    normalizedResult.columns;

  const primaryResult =
    getPrimaryResult(
      resultColumns,
      resultRows
    );

  // ==========================================================
  // UI
  // ==========================================================

  return (
    <div className="app">

      {/* ====================================================
          HEADER
      ==================================================== */}

      <header className="header">

        <div className="brand">

          <div className="brand-icon">
            AI
          </div>

          <div>
            <h1>
              AI SQL Assistant
            </h1>

            <p>
              Ask questions. Get insights.
            </p>
          </div>

        </div>

        <div className="status-badge">

          <span className="status-dot" />

          System Ready

        </div>

      </header>

      <main className="container">

        {/* ==================================================
            HERO
        ================================================== */}

        {!dataset && (
          <section className="hero">

            <span className="eyebrow">
              AI-POWERED DATA ANALYSIS
            </span>

            <h2>
              Talk to your data
              <br />

              <span>
                in plain English.
              </span>
            </h2>

            <p>
              Upload your CSV or Excel
              dataset and ask questions
              using natural language.
              Let AI generate and execute
              SQL for you.
            </p>

          </section>
        )}

        {/* ==================================================
            UPLOAD
        ================================================== */}

        {!dataset && (
          <section className="upload-card">

            <div
              className={`drop-zone ${
                dragActive
                  ? "drag-active"
                  : ""
              }`}
              onDragOver={
                handleDragOver
              }
              onDragLeave={
                handleDragLeave
              }
              onDrop={
                handleDrop
              }
              onClick={() =>
                fileInputRef.current?.click()
              }
            >

              <div className="upload-icon">
                ↑
              </div>

              <h3>
                Drop your dataset here
              </h3>

              <p>
                or click to browse files
              </p>

              <span className="file-types">
                CSV • XLSX • XLS
              </span>

              <input
                ref={
                  fileInputRef
                }
                type="file"
                accept=".csv,.xlsx,.xls"
                hidden
                onChange={(event) =>
                  handleFileSelect(
                    event.target.files?.[0]
                  )
                }
              />

            </div>

            {file && (
              <div className="selected-file">

                <div className="file-info">

                  <div className="file-icon">
                    {file.name
                      .split(".")
                      .pop()
                      ?.toUpperCase()}
                  </div>

                  <div>

                    <strong>
                      {file.name}
                    </strong>

                    <span>
                      {(
                        file.size /
                        1024 /
                        1024
                      ).toFixed(2)}{" "}
                      MB
                    </span>

                  </div>

                </div>

                <button
                  className="primary-button"
                  onClick={(event) => {
                    event.stopPropagation();
                    handleUpload();
                  }}
                  disabled={
                    uploading
                  }
                >
                  {uploading
                    ? "Processing..."
                    : "Upload Dataset →"}
                </button>

              </div>
            )}

          </section>
        )}

        {/* ==================================================
            ERROR
        ================================================== */}

        {error && (
          <div className="error-message">

            <span>!</span>

            <div>
              {error}
            </div>

          </div>
        )}

        {/* ==================================================
            DATASET DASHBOARD
        ================================================== */}

        {dataset && (
          <>

            {/* =================================================
                DATASET HEADER
            ================================================= */}

            <section className="dataset-header">

              <div>

                <span className="eyebrow">
                  ACTIVE DATASET
                </span>

                <h2>
                  {dataset.dataset
                    ?.filename ||
                    file?.name ||
                    "Dataset"}
                </h2>

                <p>
                  Your dataset is ready
                  for analysis.
                </p>

              </div>

              <button
                className="secondary-button"
                onClick={
                  handleClear
                }
              >
                × New Dataset
              </button>

            </section>

            {/* =================================================
                STAT CARDS
            ================================================= */}

            <section className="stats-grid">

              <div className="stat-card">

                <span>
                  ROWS
                </span>

                <strong>
                  {dataset.dataset
                    ?.rows ??
                    "—"}
                </strong>

              </div>

              <div className="stat-card">

                <span>
                  COLUMNS
                </span>

                <strong>
                  {dataset.dataset
                    ?.columns ??
                    "—"}
                </strong>

              </div>

              <div className="stat-card">

                <span>
                  FILE TYPE
                </span>

                <strong>
                  {file?.name
                    ?.split(".")
                    .pop()
                    ?.toUpperCase() ||
                    "DATA"}
                </strong>

              </div>

              <div className="stat-card">

                <span>
                  STATUS
                </span>

                <strong className="success-text">
                  ● Ready
                </strong>

              </div>

            </section>

            {/* =================================================
                DATA PREVIEW
            ================================================= */}

            <section className="panel">

              <div className="panel-header">

                <div>

                  <span className="eyebrow">
                    DATA
                  </span>

                  <h3>
                    Dataset Preview
                  </h3>

                </div>

                <span className="preview-label">
                  First 5 rows
                </span>

              </div>

              {previewRows.length > 0 ? (

                <div className="table-wrapper">

                  <table className="data-table">

                    <thead>
                      <tr>

                        {previewColumns.map(
                          (column) => (
                            <th
                              key={column}
                            >
                              {formatColumnName(
                                column
                              )}
                            </th>
                          )
                        )}

                      </tr>
                    </thead>

                    <tbody>

                      {previewRows.map(
                        (
                          row,
                          rowIndex
                        ) => (

                          <tr
                            key={
                              rowIndex
                            }
                          >

                            {previewColumns.map(
                              (column) => (

                                <td
                                  key={
                                    column
                                  }
                                >
                                  {formatCellValue(
                                    row[column]
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

                <div className="empty-state">
                  No preview data available.
                </div>

              )}

            </section>

            {/* =================================================
                ASK AI
            ================================================= */}

            <section className="ask-section">

              <div className="ask-header">

                <div>

                  <span className="eyebrow">
                    AI ANALYSIS
                  </span>

                  <h2>
                    Ask your dataset
                  </h2>

                  <p>
                    Ask anything about
                    your data in natural
                    language.
                  </p>

                </div>

              </div>

              <div className="question-box">

                <textarea
                  value={
                    question
                  }
                  onChange={(event) =>
                    setQuestion(
                      event.target.value
                    )
                  }
                  onKeyDown={(event) => {

                    if (
                      event.key ===
                        "Enter" &&
                      !event.shiftKey
                    ) {
                      event.preventDefault();

                      handleAsk();
                    }

                  }}
                  placeholder="e.g. What are the total sales by city?"
                  rows="3"
                  disabled={
                    asking
                  }
                />

                <div className="question-footer">

                  <span>
                    {asking
                      ? "AI is analyzing your dataset..."
                      : "Press Enter to ask"}
                  </span>

                  <button
                    className="primary-button"
                    onClick={
                      handleAsk
                    }
                    disabled={
                      asking ||
                      !question.trim()
                    }
                  >
                    {asking
                      ? "Analyzing..."
                      : "Ask AI →"}
                  </button>

                </div>

              </div>

            </section>

            {/* =================================================
                AI RESULT
            ================================================= */}

            {answer && (
              <section className="results-section">

                <div className="result-heading">

                  <span className="eyebrow">
                    AI RESPONSE
                  </span>

                  <h2>
                    Analysis Result
                  </h2>

                </div>

                {/* =================================================
                    QUESTION
                ================================================= */}

                <div className="question-result">

                  <span>
                    YOUR QUESTION
                  </span>

                  <p>
                    {formatCellValue(
                      answer.question
                    )}
                  </p>

                </div>

                {/* =================================================
                    PRIMARY RESULT
                ================================================= */}

                {primaryResult && (
                  <div className="primary-result-card">

                    <span>
                      {formatColumnName(
                        primaryResult.column
                      )}
                    </span>

                    <strong>
                      {formatCellValue(
                        primaryResult.value
                      )}
                    </strong>

                  </div>
                )}

                {/* =================================================
                    SQL
                ================================================= */}

                {answer.sql && (
                  <div className="result-card">

                    <div className="result-card-header">

                      <h3>
                        Generated SQL
                      </h3>

                      <span>
                        SQL
                      </span>

                    </div>

                    <pre className="sql-code">
                      {formatCellValue(
                        answer.sql
                      )}
                    </pre>

                  </div>
                )}

                {/* =================================================
                    QUERY RESULT
                ================================================= */}

                <div className="result-card">

                  <div className="result-card-header">

                    <h3>
                      Query Result
                    </h3>

                    <span>
                      {normalizedResult.rowCount}{" "}
                      {normalizedResult.rowCount === 1
                        ? "row"
                        : "rows"}
                    </span>

                  </div>

                  {resultRows.length > 0 ? (

                    <div className="table-wrapper">

                      <table className="data-table">

                        <thead>

                          <tr>

                            {resultColumns.map(
                              (column) => (

                                <th
                                  key={
                                    column
                                  }
                                >
                                  {formatColumnName(
                                    column
                                  )}
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
                                  (column) => (

                                    <td
                                      key={
                                        column
                                      }
                                    >
                                      {formatCellValue(
                                        row[column]
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

                    <pre className="raw-result">
                      {JSON.stringify(
                        answer.result,
                        null,
                        2
                      )}
                    </pre>

                  )}

                </div>

                {/* =================================================
                    INSIGHT
                ================================================= */}

                {answer.insight && (
                  <div className="result-card insight-card">

                    <div className="result-card-header">

                      <h3>
                        AI Insight
                      </h3>

                      <span>
                        INSIGHT
                      </span>

                    </div>

                    <p>
                      {answer.insight}
                    </p>

                  </div>
                )}

                {/* =================================================
                    QUERY HISTORY
                ================================================= */}

                {answer.query_history_id && (
                  <div className="history-id">

                    Query ID:{" "}

                    {formatCellValue(
                      answer.query_history_id
                    )}

                  </div>
                )}

              </section>
            )}

          </>
        )}

      </main>

      {/* ======================================================
          FOOTER
      ====================================================== */}

      <footer className="footer">
        AI SQL Assistant • Intelligent
        Data Analysis
      </footer>

    </div>
  );
}

export default App;