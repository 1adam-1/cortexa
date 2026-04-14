import { useState } from "react";
import classes from "./Notebook.module.css";
import { Send, Sparkles, MessageSquare, Settings, Layout } from "lucide-react";
import { useParams } from "react-router-dom";

const [question, setQuestion] = useState();

const session_id = useParams().sessionId;

const handleSend = async () => {
  try {
    const response = await fetch("http://localhost:5000/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: question,
        session_id: session_id
     }),
    });

    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
};

export default function Notebook() {
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
                    <div className={classes.welcomeState}>
                        <div className={classes.iconContainer}>
                            <Sparkles className={classes.welcomeIcon} />
                        </div>
                        <h3>How can I help you today?</h3>
                        <p>Ask anything about your notes, brainstorm ideas, or generate summaries.</p>
                    </div>
                    {/* Chat messages would go here */}
                </div>

                <div className={classes.chatInputContainer}>
                    <div className={classes.inputWrapper}>
                        <input 
                            type="text" 
                            placeholder="Message Cortexa..." 
                            className={classes.chatInput}
                            onChange={(e) => setQuestion(e.target.value)}
                        />
                        <button className={classes.sendBtn}
                            onClick={handleSend}
                        >
                            <Send size={16} />
                        </button>
                    </div>
                    <p className={classes.disclaimer}>
                        Cortexa can make mistakes. Consider verifying important information.
                    </p>
                </div> 
            </div>

            <div className={classes.studio}>
                <div className={classes.studioHeader}>
                    <div className={classes.headerTitle}>
                        <Layout className={classes.headerIconStudio} />
                        <h2>Studio</h2>
                    </div>
                </div>
                <div className={classes.studioContent}>
                    <div className={classes.placeholderCard}>
                        <p>Detailed analysis and tools will appear here</p>
                    </div>
                </div>
            </div>
        </div>
    );
}