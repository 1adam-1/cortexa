import { Button } from '../ui/button.tsx';
import { useEffect, useState } from 'react';
import {
    Card,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle
} from "@/components/ui/card.tsx";
import { Plus, BookOpen } from "lucide-react";
import classes from './Notebook.module.css';

import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { useNavigate } from "react-router-dom";
import { Trash2 } from "lucide-react";

export default function Notebooks() {
    const navigate = useNavigate();
    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [sessions, setSessions] = useState([]);
    const [idSession, setIdSession] = useState(null);

    //get user id
    const user = localStorage.getItem("user");
    const userId = user ? JSON.parse(user).id : null;

   const fetchSessions = async () => {
            if (!userId) return;
            const token = localStorage.getItem("access_token");
            const response = await fetch(`http://localhost:5000/auth/sessions/${userId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.status === 401 || response.status === 403) {
                alert("Session expirée ou accès refusé.");
                navigate("/auth");
                return;
            }

            const data = await response.json();
            setSessions(data);
        };

    //fetch sessions
    useEffect(() => {
        
        fetchSessions();
    }, [userId]);

    //upload file
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
            // STEP 1: Upload the file
            const formData = new FormData();
            formData.append("file", selectedFile);
            
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

            setIdSession(uploadData.id_session); // Keeping this if you need it elsewhere

            // STEP 2: Process the document using the ID returned
            setIsUploading(false);
            setIsProcessing(true); // Switch to processing state

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
                alert("Fichier envoyé et traité avec succès au RAG !");
                setSelectedFile(null);
                navigate(`/Notebook/${uploadData.id_session}`);
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
        } finally {
            setIsUploading(false);
            setIsProcessing(false);
            
        }
        
    };

     //delete session
    const handleDelete = async (id_session) => {
    try {
        const token = localStorage.getItem("access_token");

        const response = await fetch(
            `http://localhost:5000/auth/deleteSession/${id_session}`,
            {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            throw new Error("Failed to delete session");
        }

        fetchSessions();

    } catch (error) {
        console.error("Error deleting session:", error);
    }
};

    return (
        <div className={classes.Notebooks}>
            <div className={classes.header}>
                <div>
                    <h1 className={classes.title}>Notebooks</h1>
                    <p className={classes.subtitle}>
                        Create and manage your knowledge bases from various sources
                    </p>
                </div>
            </div>
            
            <div className={classes.cards}>

                <div className={`${classes.cardBase} ${classes.createCard}`}>
                    <div className={classes.iconWrapper}>
                        <Plus className={classes.icon} />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">Create Notebook</h3>
                    <p className="text-zinc-400 text-sm text-center mb-6">
                        Build a new knowledge base from your sources
                    </p>

                    <Dialog>
                        <DialogTrigger asChild>
                            <Button className={classes.createButton}>
                                <Plus size={18} className="mr-2" /> New Notebook
                            </Button>
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
                </div>

                {/* Displaying User Sessions */}
                {sessions && sessions.length > 0 && sessions.map((session) => (
                    <div 
                        key={session.id} 
                        className={classes.cardBase}
                        onClick={() => navigate(`/Notebook/${session.id}`)}
                    >
                        <div className="p-8 h-full flex flex-col cursor-pointer">
                            <div className="h-12 w-12 rounded-xl bg-white text-black flex items-center justify-center mb-6">
                                <BookOpen size={24} />
                            </div>
                            
                            <h3 className="text-xl font-bold text-white mb-2">Notebook #{session.id}</h3>
                            <p className="text-zinc-400 text-sm mb-auto">
                                Created on {new Date(session.date_debut).toLocaleDateString(undefined, {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric'
                                })}
                            </p>

                            <div className="mt-8 pt-6 border-t border-white/5 flex items-center justify-between">
                                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                                    {session.documents?.length || 0} Documents
                                </span>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="text-zinc-600 hover:text-white hover:bg-white/5 transition-colors"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleDelete(session.id);
                                    }}
                                    title="Delete Notebook"
                                >
                                    <Trash2 size={18} />
                                </Button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}