import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import classes from "./Notebook.module.css";
import { Send, Sparkles, MessageSquare, Settings, Layout, Square, FilePlus, Plus } from "lucide-react";
import { useParams, useNavigate } from "react-router-dom";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog.tsx";
import { Button } from "../ui/button.tsx";

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
    const [storedQCMs, setStoredQCMs] = useState([]); 
    const [userAnswers, setUserAnswers] = useState({});
    const [showResults, setShowResults] = useState(false);
    const [isGeneratingQCM, setIsGeneratingQCM] = useState(false);
    const [numQuestions, setNumQuestions] = useState(5);
    const [difficulty, setDifficulty] = useState("moyen");

    const [practiceTopic, setPracticeTopic] = useState("");
    const [practiceQuestion, setPracticeQuestion] = useState(null);
    const [practiceAnswer, setPracticeAnswer] = useState("");
    const [practiceEvaluation, setPracticeEvaluation] = useState(null);
    const [isGeneratingPractice, setIsGeneratingPractice] = useState(false);
    const [isEvaluatingPractice, setIsEvaluatingPractice] = useState(false);
    const [showPracticeModal, setShowPracticeModal] = useState(false);

    // Summary specific states
    const [summaryData, setSummaryData] = useState(null);
    const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
    const [storedSummaries, setStoredSummaries] = useState([]);

    // Upload specific states
    const [showUploadModal, setShowUploadModal] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);

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
                        session_id: sessionId,
                        num_questions: numQuestions,
                        difficulty: difficulty
                    })

            });

            const data = await response.json();
            if (data.qcm) {
                setQcmData(data.qcm);
                setUserAnswers({});
                setShowResults(false);
                setShowModal(false);
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

     const generatePracticeQuestion = async () => {
        try {
            setIsGeneratingPractice(true);
            const token = localStorage.getItem("access_token");

            const requestBody = { session_id: sessionId };
            if (practiceTopic && practiceTopic.trim().length > 0) {
                requestBody.topic = practiceTopic.trim();
            }

            const response = await fetch ('http://localhost:5000/api/studio/practice/question', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            if (data.question) {
                setPracticeQuestion(data.question);
                setPracticeAnswer("");
                setPracticeEvaluation(null);
                setShowPracticeModal(false);
            }
        } catch (error) {
            console.error("Error generating practice question:", error);
            alert("Failed to generate question.");
        } finally {
            setIsGeneratingPractice(false);
        }
    };

    const evaluatePracticeAnswer = async () => {
        try {
            setIsEvaluatingPractice(true);
            const token = localStorage.getItem("access_token");

            const response = await fetch ('http://localhost:5000/api/studio/practice/evaluate', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    question: practiceQuestion,
                    user_answer: practiceAnswer
                })
            });

            const data = await response.json();
            if (data.evaluation) {
                setPracticeEvaluation(data.evaluation);
            }
        } catch (error) {
            console.error("Error evaluating practice answer:", error);
            alert("Failed to evaluate answer.");
        } finally {
            setIsEvaluatingPractice(false);
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

    const handleFileChange = (event) => {
        if (event.target.files && event.target.files[0]) {
            setSelectedFile(event.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            alert("Veuillez d'abord sélectionner un fichier.");
            return;
        }
        
        setIsUploading(true);
        try {
            const formData = new FormData();
            formData.append("file", selectedFile);
            formData.append("id_session", sessionId);
            
            const token = localStorage.getItem("access_token");
            if (!token) {
                alert("Session expirée. Veuillez vous reconnecter.");
                navigate("/auth");
                return;
            }

            const uploadResponse = await fetch('http://localhost:5000/api/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData,
            });
            const uploadData = await uploadResponse.json();
            
            if (!uploadResponse.ok) {
                alert(`Erreur d'upload : ${uploadData.message || uploadData.error}`);
                setIsUploading(false);
                return;
            }

            setIsUploading(false);
            setIsProcessing(true);

            const processResponse = await fetch('http://localhost:5000/api/processing', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ id_document: uploadData.id_document })
            });

            const processData = await processResponse.json();

            setIsProcessing(false);

            if (processResponse.ok) {
                alert("Fichier ajouté et traité avec succès au RAG !");
                setSelectedFile(null);
                setShowUploadModal(false);
            } else {
                if (processResponse.status === 403) {
                    alert("Accès refusé. Vous n'êtes pas autorisé à effectuer cette action.");
                } else {
                    alert(`Erreur de traitement : ${processData.message}`);
                }
            }

        } catch (error) {
            console.error("Erreur lors de l'envoi :", error);
            alert("Erreur de connexion avec le serveur.");
            setIsUploading(false);
            setIsProcessing(false);
        }
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

    
      //Summary generation
    const handle_summary=async()=>{
        try{
            setIsGeneratingSummary(true);
            const token = localStorage.getItem("access_token");

            const response = await fetch("http://localhost:5000/api/studio/summary", {
                method: "POST", 
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.summary) {
                setSummaryData(data.summary);
                fetchSummaries(); // Refresh the list of summaries
            }

            setIsGeneratingSummary(false);

        }catch(error){
            console.error("Failed to generate summary:", error);
            setIsGeneratingSummary(false);
        }
    }

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

    //fetch stored summaries
    const fetchSummaries = async () => {
        if (!sessionId || sessionId === "null") return;
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`http://localhost:5000/api/generation/summary/${sessionId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await response.json();
            setStoredSummaries(data.summaries || []);
        } catch (error) {
            console.error("Failed to fetch stored summaries:", error);
        }
    };

    useEffect(() => {
        


        fetchHistory();
        fetchQCM();
        fetchSummaries();
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
                        <Dialog open={showUploadModal} onOpenChange={setShowUploadModal}>
                            <DialogTrigger asChild>
                                <button className={classes.iconBtn} title="Add Document">
                                    <FilePlus size={18} />
                                </button>
                            </DialogTrigger>
                            <DialogContent className="sm:max-w-md bg-zinc-950 border-zinc-800">
                                <DialogHeader>
                                    <DialogTitle className="text-white">Upload Files</DialogTitle>
                                </DialogHeader>
                                <div className="flex flex-col gap-4 mt-4">
                                    <div className="border-2 border-dashed border-zinc-800 rounded-xl p-12 flex flex-col items-center justify-center hover:border-zinc-700 transition-colors cursor-pointer group">
                                        <input
                                            type="file"
                                            className="hidden"
                                            id="fileUpload"
                                            onChange={handleFileChange} 
                                        />
                                        <label htmlFor="fileUpload" className="flex flex-col items-center cursor-pointer">
                                            <div className="h-12 w-12 rounded-full bg-zinc-900 flex items-center justify-center mb-4 group-hover:bg-white group-hover:text-black transition-all">
                                                <Plus size={24} />
                                            </div>
                                            <span className="text-zinc-400 font-medium">
                                                {selectedFile ? selectedFile.name : "Click to select or drag and drop"}
                                            </span>
                                        </label>
                                    </div>
                                    <Button 
                                        className="w-full bg-white text-black hover:bg-zinc-200 transition-colors font-bold h-12 rounded-xl"
                                        onClick={handleUpload} 
                                        disabled={isUploading || isProcessing || !selectedFile}  
                                    >
                                        {isUploading ? "Uploading..." : isProcessing ? "Processing (This takes a while)..." : "Upload to RAG"}
                                    </Button>
                                </div>
                            </DialogContent>
                        </Dialog>
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
                                        <div className={classes.messageContent}> <ReactMarkdown>{msg.content}</ReactMarkdown></div>
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
                    {!qcmData && !practiceQuestion && !summaryData ? (
                        <div className={classes.studioOverview}>
                            <div className={classes.studioEmpty}>
                                <div className={classes.studioCard} onClick={() => setShowModal(true)}>
                                    <h3>Generate New QCM</h3>
                                    <p>Create a multiple-choice quiz based on your documents to test your knowledge.</p>
                                </div>
                                <div className={classes.studioCard} onClick={() => setShowPracticeModal(true)}>
                                    <h3>Practice Mode</h3>
                                    <p>Generate an open-ended question to deeply test your comprehension.</p>
                                </div>
                                <div 
                                    className={classes.studioCard} 
                                    onClick={isGeneratingSummary ? undefined : handle_summary}
                                    style={{ opacity: isGeneratingSummary ? 0.7 : 1, cursor: isGeneratingSummary ? 'auto' : 'pointer' }}
                                >
                                    {isGeneratingSummary ? (
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                            <span className={classes.spinner} style={{ borderColor: 'rgba(255,255,255,0.3)', borderTopColor: '#fff' }}></span>
                                            <h3>Generating Summary...</h3>
                                        </div>
                                    ) : (
                                        <>
                                            <h3>Generate Summary</h3>
                                            <p>Create a concise summary of the documents from this session.</p>
                                        </>
                                    )}
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

                            {/* Insert your stored Summaries array mapping here */}
                            {storedSummaries && storedSummaries.length > 0 && (
                                <div className={classes.storedQcmSection}>
                                    <h3 className={classes.storedQcmTitle}>Your Saved Summaries</h3>
                                    <div className={classes.storedQcmGrid}>
                                        {storedSummaries.map((summaryRecord, index) => {
                                            return (
                                            <div 
                                                key={summaryRecord.id || index} 
                                                className={classes.storedQcmItem}
                                                onClick={() => {
                                                    setSummaryData(summaryRecord.output); 
                                                }}
                                            >
                                                <h4>Summary #{index + 1}</h4>
                                                <p>{new Date(summaryRecord.created_at).toLocaleDateString()}</p>
                                            </div>
                                        )})}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : qcmData ? (
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
                    ) : practiceQuestion ? (
                        <div className={classes.qcmContainer}>
                            <div className={classes.qcmHeader}>
                                <h3>Practice Question</h3>
                            </div>
                            
                            <div className={classes.qcmList} style={{ padding: "20px" }}>
                                <h4 style={{ marginBottom: "15px", fontSize: "1.1rem" }}><ReactMarkdown>{practiceQuestion}</ReactMarkdown></h4>
                                
                                {!practiceEvaluation && (
                                    <textarea
                                        style={{ width: "100%", minHeight: "120px", padding: "15px", borderRadius: "8px", border: "1px solid #ccc", marginBottom: "15px", fontFamily: "inherit" }}
                                        placeholder="Type your answer here... (e.g. key concepts, definitions)"
                                        value={practiceAnswer}
                                        onChange={(e) => setPracticeAnswer(e.target.value)}
                                        disabled={isEvaluatingPractice}
                                    />
                                )}

                                {practiceEvaluation && (
                                    <div style={{ marginTop: "20px", padding: "15px", backgroundColor: practiceEvaluation.status === "Correct" ? "#d4edda" : practiceEvaluation.status === "Partial" ? "#fff3cd" : "#f8d7da", borderRadius: "8px", color: practiceEvaluation.status === "Correct" ? "#155724" : practiceEvaluation.status === "Partial" ? "#856404" : "#721c24" }}>
                                        <h4 style={{ marginBottom: "10px", fontWeight: "bold" }}>
                                            Result: {practiceEvaluation.status}
                                        </h4>
                                        <p style={{ marginBottom: "10px", lineHeight: "1.5" }}><strong>Feedback:</strong> {practiceEvaluation.feedback}</p>
                                        <p style={{ lineHeight: "1.5" }}><strong>Expected Answer:</strong> {practiceEvaluation.expected_answer}</p>
                                    </div>
                                )}
                            </div>

                            <div className={classes.qcmActions}>
                                {!practiceEvaluation ? (
                                    <button 
                                        className={classes.checkAnswersBtn}
                                        onClick={evaluatePracticeAnswer}
                                        disabled={!practiceAnswer.trim() || isEvaluatingPractice}
                                        style={{ opacity: (!practiceAnswer.trim() || isEvaluatingPractice) ? 0.5 : 1 }}
                                    >
                                        {isEvaluatingPractice ? "Evaluating..." : "Check Answer"}
                                    </button>
                                ) : (
                                    <button 
                                        className={classes.checkAnswersBtn}
                                        onClick={generatePracticeQuestion}
                                        disabled={isGeneratingPractice}
                                    >
                                        {isGeneratingPractice ? "Generating..." : "Next Question"}
                                    </button>
                                )}
                                <button 
                                    className={classes.newQcmBtn}
                                    onClick={() => { setPracticeQuestion(null); setPracticeEvaluation(null); setPracticeTopic(""); }}
                                    disabled={isGeneratingPractice || isEvaluatingPractice}
                                >
                                    Close Practice
                                </button>
                            </div>
                        </div>
                    ) : summaryData ? (
                        <div className={classes.qcmContainer}>
                            <div className={classes.qcmHeader}>
                                <h3>Document Summary</h3>
                            </div>
                            <div className={classes.qcmList} style={{ padding: "20px", overflowY: "auto" }}>
                                <div style={{ lineHeight: "1.6" }}>
                                    <ReactMarkdown>{summaryData}</ReactMarkdown>
                                </div>
                            </div>
                            <div className={classes.qcmActions}>
                                <button 
                                    className={classes.newQcmBtn}
                                    onClick={() => setSummaryData(null)}
                                >
                                    Close Summary
                                </button>
                            </div>
                        </div>
                    ) : null}
                </div>
            </div>

            {/* Modal Overlay */}
            {showModal && (
                <div className={classes.modalOverlay}>
                    {/* Modal Content */}
                    <div className={classes.modalContent}>
                        <h3 className={classes.modalTitle}>Generate QCM</h3>
                        <p className={classes.modalDescription}>Generate a multi-choice questionnaire to test your understanding of the current documents. This might take a few seconds.</p>
                        
                        <div className={classes.modalOptionsContainer}>
                            <div className={classes.modalOptionGroup}>
                                <label className={classes.modalLabel}>Number of questions:</label>
                                <div className={classes.modalButtonGroup}>
                                    <button 
                                        className={`${classes.modalOptionBtn} ${numQuestions === 5 ? classes.modalOptionBtnSelected : ''}`}
                                        onClick={() => setNumQuestions(5)}
                                    >5</button>
                                    <button 
                                        className={`${classes.modalOptionBtn} ${numQuestions === 15 ? classes.modalOptionBtnSelected : ''}`}
                                        onClick={() => setNumQuestions(15)}
                                    >15</button>
                                    <button 
                                        className={`${classes.modalOptionBtn} ${numQuestions === 20 ? classes.modalOptionBtnSelected : ''}`}
                                        onClick={() => setNumQuestions(20)}
                                    >20</button>
                                </div>
                                <label className={classes.modalLabel}>Type:</label>
                                <div className={classes.modalButtonGroup}>
                                    <button 
                                        className={`${classes.modalOptionBtn} ${numQuestions === 5 ? classes.modalOptionBtnSelected : ''}`}
                                        onClick={() => setNumQuestions(5)}
                                    >QCU</button>
                                    <button 
                                        className={`${classes.modalOptionBtn} ${numQuestions === 1 ? classes.modalOptionBtnSelected : ''}`}
                                       
                                    >QCM</button>
                                  
                                </div>

                            </div>

                            <div className={classes.modalOptionGroup}>
                                <label className={classes.modalLabel}>Difficulty:</label>
                                <div className={classes.modalButtonGroup}>
                                    <button 
                                        className={`${classes.modalOptionBtn} ${difficulty === 'facile' ? classes.modalOptionBtnSelected : ''}`}
                                        onClick={() => setDifficulty('facile')}
                                    >Facile</button>
                                    <button 
                                        className={`${classes.modalOptionBtn} ${difficulty === 'moyen' ? classes.modalOptionBtnSelected : ''}`}
                                        onClick={() => setDifficulty('moyen')}
                                    >Moyen</button>
                                    <button 
                                        className={`${classes.modalOptionBtn} ${difficulty === 'difficile' ? classes.modalOptionBtnSelected : ''}`}
                                        onClick={() => setDifficulty('difficile')}
                                    >Difficile</button>
                                </div>
                            </div>
                        </div>

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

            {/* Practice Modal Overlay */}
            {showPracticeModal && (
                <div className={classes.modalOverlay}>
                    {/* Modal Content */}
                    <div className={classes.modalContent}>
                        <h3 className={classes.modalTitle}>Generate Practice Question</h3>
                        <p className={classes.modalDescription}>Get a single, open-ended question to test your knowledge.</p>
                        
                        <div style={{ marginTop: "15px", marginBottom: "20px" }}>
                            <label style={{ display: "block", marginBottom: "5px", fontSize: "0.9rem", fontWeight: "bold" }}>Optional Focus Topic</label>
                            <input 
                                type="text"
                                style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #ccc", fontFamily: "inherit" }}
                                placeholder="e.g. 'Chapter 2' or 'Machine Learning'"
                                value={practiceTopic}
                                onChange={(e) => setPracticeTopic(e.target.value)}
                                disabled={isGeneratingPractice}
                            />
                        </div>

                        <div className={classes.modalActions}>
                            <button 
                                className={classes.modalBtnCancel}
                                onClick={() => setShowPracticeModal(false)}
                                disabled={isGeneratingPractice}
                            >
                                Cancel
                            </button>
                            <button 
                                className={classes.modalBtnGenerate}
                                onClick={generatePracticeQuestion}
                                disabled={isGeneratingPractice}
                            >
                                {isGeneratingPractice ? (
                                    <>
                                        <span className={classes.spinner}></span>
                                        Generating...
                                    </>
                                ) : (
                                    "Generate Question"
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
