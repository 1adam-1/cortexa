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

export default function Notebooks() {
    const navigate = useNavigate();
    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [sessions, setSessions] = useState([]);

    //get user id
    const user = localStorage.getItem("user");
    const userId = user ? JSON.parse(user).id : null;

    //fetch sessions
    useEffect(() => {
        const fetchSessions = async () => {
            if (!userId) return;
            const token = localStorage.getItem("access_token");
            const response = await fetch(`http://localhost:5000/auth/sessions/${userId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            const data = await response.json();
            setSessions(data);
        };
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

            const uploadResponse = await fetch('/api/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData,
            });
            const uploadData = await uploadResponse.json();
            
            if (!uploadResponse.ok) {
                alert(`Erreur d'upload : ${uploadData.message || uploadData.error}`);
                return;
            }

            // STEP 2: Process the document using the ID returned
            setIsUploading(false);
            setIsProcessing(true); // Switch to processing state

            const processResponse = await fetch('/api/processing', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ id_document: uploadData.id_document })
            });

            const processData = await processResponse.json();

            if (processResponse.ok) {
                alert("Fichier envoyé et traité avec succès au RAG !");
                console.log(processData);
                setSelectedFile(null);
            } else {
                alert(`Erreur de traitement : ${processData.message}`);
            }

        } catch (error) {
            console.error("Erreur lors de l'envoi :", error);
            alert("Erreur de connexion avec le serveur.");
        } finally {
            setIsUploading(false);
            setIsProcessing(false);
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

                <Card className={`${classes.createCard} w-[350px]`}>
                    <CardHeader className={classes.cardHeader}>
                        <div className={classes.iconWrapper}>
                            <Plus className={classes.icon} />
                        </div>
                        <CardTitle>Create Notebook</CardTitle>
                        <CardDescription>
                            Build a new notebook from your sources
                        </CardDescription>
                    </CardHeader>

                    <CardFooter>
                        <Dialog>
                            <DialogTrigger asChild>
                                <Button className={classes.createButton}>
                                    <Plus size={18} /> New Notebook
                                </Button>
                            </DialogTrigger>

                             <DialogContent className="sm:max-w-md">
                                <DialogHeader>
                                    <DialogTitle>Upload Files</DialogTitle>
                                </DialogHeader>
                                <div className="flex flex-col gap-4">
                                    <input
                                        type="file"
                                        className="border p-2 rounded-md h-56 cursor-pointer"
                                        id="fileUpload"
                                        onChange={handleFileChange} 
                                    />
                                    <Button 
                                        onClick={handleUpload} 
                                        disabled={isUploading || isProcessing || !selectedFile}  
                                    >
                                        {isUploading ? "Uploading..." : isProcessing ? "Processing (This takes a while)..." : "Upload au RAG"}
                                    </Button>
                                </div>
                            </DialogContent>
                        </Dialog>
                    </CardFooter>
                </Card>

                {/* Displaying User Sessions */}
                {sessions && sessions.length > 0 && sessions.map((session) => (
                    <a onClick={() => navigate(`/notebook/${session.id}`)}>
                    <Card key={session.id} className="w-[350px] flex flex-col justify-between shadow-sm border border-border/50 backdrop-blur-xl bg-card/40 hover:bg-card/80 transition-all hover:shadow-md cursor-pointer">
                        <CardHeader className="pb-4">
                            <div className="h-10 w-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center mb-4">
                                <BookOpen size={20} />
                            </div>
                            <CardTitle>Notebook #{session.id}</CardTitle>
                            <CardDescription>
                                Created: {new Date(session.date_debut).toLocaleDateString()}
                            </CardDescription>
                        </CardHeader>
                        <CardFooter className="pt-0">
                            <div className="flex flex-col gap-2 w-full">
                                <div className="flex items-center text-sm text-muted-foreground border-t pt-4">
                                    <span className="bg-secondary/50 px-2.5 py-1 rounded-md font-medium text-xs">
                                        {session.documents?.length || 0} Document(s)
                                    </span>
                                </div>
                            </div>
                        </CardFooter>
                    </Card>
                    </a>
                ))}
            </div>
        </div>
    );
}