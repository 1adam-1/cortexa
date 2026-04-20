import { useState, useEffect, useRef } from "react";
import classes from "./Notebook.module.css";
import { Send, Sparkles, MessageSquare, Settings, Layout, Square } from "lucide-react";
import { useParams, useNavigate } from "react-router-dom";

export default function Notebook() {
    const navigate = useNavigate();
    const [question, setQuestion] = useState("");
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const { sessionId } = useParams();
    const abortControllerRef = useRef(null);
    const [isStreaming, setIsStreaming] = useState(false);
    const [showModal, setShowModal] = useState(false);
    const [qcmData, setQcmData] = useState(null);
    const [storedQCMs, setStoredQCMs] = useState([]); // State for stored QCMs
    const [userAnswers, setUserAnswers] = useState({});
    const [showResults, setShowResults] = useState(false);
    const [isGeneratingQCM, setIsGeneratingQCM] = useState(false);


    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const generateQCM = async () => {
        try {
            setIsGeneratingQCM(true);
            const token = localStorage.getItem("access_token");

            const response = await fetch ('http://localhost:5000/api/studio/qcm', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: 
                    JSON.stringify({
                        session_id: sessionId
                    })

            });

            const data = await response.json();
            if (data.qcm) {
                setQcmData(data.qcm);
                setUserAnswers({});
                setShowResults(false);
                setShowModal(false);
                // Refresh the stored QCM list to show the new one
                fetchQCM();
            }
            setIsGeneratingQCM(false);
        }
        catch (error) {
            console.error("Erreur lors de la generation du QCM :", error);
            alert("Erreur lors de la generation du QCM.");
            setIsGeneratingQCM(false);
        }
    }

    const handleAnswerSelect = (questionIndex, optionKey) => {
        if (!showResults) {
            setUserAnswers(prev => ({
                ...prev,
                [questionIndex]: optionKey
            }));
        }
    };

    const calculateScore = () => {
        if (!qcmData) return 0;
        let score = 0;
        qcmData.forEach((q, index) => {
            if (userAnswers[index] === q.correct_answer) {
                score++;
            }
        });
        return score;
    };

    //fetch chat history
    const fetchHistory = async () => {
        if (!sessionId || sessionId === "null") return;
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`http://localhost:5000/api/sessions/${sessionId}/messages`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
                    
                    if (response.status === 401 || response.status === 403) {
                        alert("Accès refusé ou session expirée.");
                        navigate("/Notebooks");
                        return;
                    }

                    const data = await response.json();
                    setMessages(data);
                } catch (error) {
                    console.error("Failed to fetch chat history:", error);
                }
            };

    
    //fetch stored QCMs
    const fetchQCM = async () => {
        if (!sessionId || sessionId === "null") return;
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`http://localhost:5000/api/generation/qcm/${sessionId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await response.json();
            setStoredQCMs(data.qcms || []);
        } catch (error) {
            console.error("Failed to fetch stored QCMs:", error);
        }
    };

    useEffect(() => {
        


        fetchHistory();
        fetchQCM();
    }, [sessionId]);

    const handleSend = async () => {
        if (!question.trim()) return;

         if (abortControllerRef.current) {
        abortControllerRef.current.abort();
         }

         const controller = new AbortController();
         abortControllerRef.current = controller;

        const userMsg = {
            id: Date.now(),
            role: "user",
            content: question,
            created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMsg]);
        setQuestion("");
        setIsLoading(true);
        setIsStreaming(true);

        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch("http://localhost:5000/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: question,
                    session_id: sessionId
                }),
                signal: controller.signal
            });

            if (response.status === 403) {
                alert("Vous n'êtes pas autorisé à envoyer des messages dans cette session.");
                setIsLoading(false);
                setIsStreaming(false);
                return;
            }
            
            const assistantMsg = {
                id: Date.now() + 1,
                role: "assistant",
                content: "",
                created_at: new Date().toISOString()
            };
            setMessages(prev => [...prev, assistantMsg]);

            setIsLoading(false); 

             // 2. Read the stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = "";
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            // Flask sends "data: text\n\n", so we need to clean it
            const lines = chunk.split("\n");
            
            lines.forEach(line => {
                if (line.startsWith("data: ")) {
                    const content = line.replace("data: ", "");
                    fullContent += content;
                    // 3. Update the specific message in the state
                    setMessages(prev => prev.map(msg => 
                        msg.id === assistantMsg.id
                            ? { ...msg, content: fullContent } 
                            : msg
                    ));
                }
            });
        }
    } catch (error) {
        if (error.name === "AbortError") {
            console.log("Request aborted");
        } else {
            console.error("Streaming error:", error);
        }
    } finally {
        setIsLoading(false);
        setIsStreaming(false);
        abortControllerRef.current = null;
    }
};

const handleStop = () => {
    if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        setIsLoading(false);
        setIsStreaming(false);
    }
};


    return (
        <div className={classes.wrapper}>
            <div className={classes.discussion}>
                <div className={classes.discussionHeader}>
                    <div className={classes.headerTitle}>
                        <MessageSquare className={classes.headerIcon} />
                        <h2>Discussion</h2>
                    </div>
                    <div className={classes.headerActions}>
                        <button className={classes.iconBtn}>
                            <Settings size={18} />
                        </button>
                    </div>
                </div>

                <div className={classes.chatBody}>
                    {messages.length === 0 && !isLoading ? (
                        <div className={classes.welcomeState}>
                            <div className={classes.iconContainer}>
                                <Sparkles className={classes.welcomeIcon} size={32} />
                            </div>
                            <h3>How can I help you?</h3>
                            <p>Ask anything about your documents, brainstorm ideas, or generate summaries.</p>
                        </div>
                    ) : (
                        <div className={classes.messagesContainer}>
                            {messages.map((msg) => (
                                <div 
                                    key={msg.id} 
                                    className={`${classes.messageRow} ${msg.role === 'user' ? classes.userRow : classes.assistantRow}`}
                                >
                                    <div className={`${classes.messageBubble} ${msg.role === 'user' ? classes.userMessage : classes.assistantMessage}`}>
                                        <div className={classes.messageContent}>{msg.content}</div>
                                        <span className={classes.messageTime}>
                                            {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <div className={`${classes.messageRow} ${classes.assistantRow}`}>
                                    <div className={`${classes.messageBubble} ${classes.assistantMessage}`}>
                                        <div className={classes.typingIndicator}>
                                            <span></span><span></span><span></span>
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                <div className={classes.chatInputContainer}>
                    <div className={classes.inputWrapper}>
                        <input
                            type="text"
                            placeholder="Type a message..."
                            className={classes.chatInput}
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            disabled={isLoading}
                        />
                        <button 
                            className={isStreaming ? classes.stopBtn : classes.sendBtn}
                            onClick={isStreaming ? handleStop : handleSend}
                            disabled={!isStreaming && !question.trim()}
                        >
                            {isStreaming ? <Square size={18} fill="currentColor" /> : <Send size={18} />}
                        </button>
                    </div>
                    <p className={classes.disclaimer}>
                        Cortexa AI can make mistakes. Check important info.
                    </p>
                </div>
            </div>

            <div className={classes.studio}>
                <div className={classes.studioHeader}>
                    <div className={classes.headerTitle}>
                        <Layout className={classes.headerIcon} size={20} />
                        <h2>Studio</h2>
                    </div>
                </div>
                <div className={classes.studioContent}>
                    {!qcmData ? (
                        <div className={classes.studioOverview}>
                            <div className={classes.studioEmpty}>
                                <div className={classes.studioCard} onClick={() => setShowModal(true)}>
                                    <h3>Generate New QCM</h3>
                                    <p>Create a multiple-choice quiz based on your documents to test your knowledge.</p>
                                </div>
                            </div>
                            
                            {/* Insert your stored QCMs array mapping here */}
                            {storedQCMs && storedQCMs.length > 0 && (
                                <div className={classes.storedQcmSection}>
                                    <h3 className={classes.storedQcmTitle}>Your Saved Quizzes</h3>
                                    <div className={classes.storedQcmGrid}>
                                        {storedQCMs.map((qcmRecord, index) => {
                                            let parsedData = [];
                                            try {
                                                parsedData = JSON.parse(qcmRecord.output);
                                            } catch (e) {}

                                            return (
                                            <div 
                                                key={qcmRecord.id || index} 
                                                className={classes.storedQcmItem}
                                                onClick={() => {
                                                    setQcmData(parsedData); 
                                                    setUserAnswers({});
                                                    setShowResults(false);
                                                }}
                                            >
                                                <h4>Quiz #{index + 1}</h4>
                                                <p>{parsedData.length} Questions</p>
                                            </div>
                                        )})}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className={classes.qcmContainer}>
                            <div className={classes.qcmHeader}>
                                <h3>Generated Quiz</h3>
                                {showResults && (
                                    <span className={classes.scoreBadge}>
                                        Score: {calculateScore()} / {qcmData.length}
                                    </span>
                                )}
                            </div>
                            
                            <div className={classes.qcmList}>
                                {qcmData.map((q, qIndex) => (
                                    <div key={qIndex} className={classes.qcmQuestionBox}>
                                        <h4 className={classes.qcmQuestionText}>{qIndex + 1}. {q.question}</h4>
                                        <div className={classes.qcmOptions}>
                                            {Object.entries(q.options).map(([optKey, optValue]) => {
                                                const isSelected = userAnswers[qIndex] === optKey;
                                                const isCorrect = showResults && q.correct_answer === optKey;
                                                const isWrong = showResults && isSelected && q.correct_answer !== optKey;
                                                
                                                let optionClass = classes.qcmOption;
                                                if (isSelected) optionClass += ` ${classes.qcmOptionSelected}`;
                                                if (isCorrect) optionClass += ` ${classes.qcmOptionCorrect}`;
                                                if (isWrong) optionClass += ` ${classes.qcmOptionWrong}`;

                                                return (
                                                    <div 
                                                        key={optKey} 
                                                        className={optionClass}
                                                        onClick={() => handleAnswerSelect(qIndex, optKey)}
                                                    >
                                                        <span className={classes.qcmOptionLetter}>{optKey}</span>
                                                        <span className={classes.qcmOptionText}>{optValue}</span>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className={classes.qcmActions}>
                                {!showResults ? (
                                    <button 
                                        className={classes.checkAnswersBtn}
                                        onClick={() => setShowResults(true)}
                                        disabled={Object.keys(userAnswers).length !== qcmData.length}
                                    >
                                        Check Answers
                                    </button>
                                ) : (
                                    <button 
                                        className={classes.resetQcmBtn}
                                        onClick={() => {
                                            setUserAnswers({});
                                            setShowResults(false);
                                        }}
                                    >
                                        Try Again
                                    </button>
                                )}
                                <button 
                                    className={classes.newQcmBtn}
                                    onClick={() => setQcmData(null)}
                                >
                                    Close Quiz
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Modal Overlay */}
            {showModal && (
                <div className={classes.modalOverlay}>
                    {/* Modal Content */}
                    <div className={classes.modalContent}>
                        <h3 className={classes.modalTitle}>Generate QCM</h3>
                        <p className={classes.modalDescription}>Generate a multi-choice questionnaire to test your understanding of the current documents. This might take a few seconds.</p>
                        <div className={classes.modalActions}>
                            <button 
                                className={classes.modalBtnCancel}
                                onClick={() => setShowModal(false)}
                                disabled={isGeneratingQCM}
                            >
                                Cancel
                            </button>
                            <button 
                                className={classes.modalBtnGenerate}
                                onClick={generateQCM}
                                disabled={isGeneratingQCM}
                            >
                                {isGeneratingQCM ? (
                                    <>
                                        <span className={classes.spinner}></span>
                                        Generating...
                                    </>
                                ) : (
                                    "Generate Quiz"
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
