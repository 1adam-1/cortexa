import { Button } from '../ui/button.tsx';
import { useState } from 'react';
import {
    Card,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle
} from "@/components/ui/card.tsx";
import { Plus } from "lucide-react";
import classes from './Notebook.module.css';

import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";

export default function Notebooks() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);

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
            </div>
        </div>
    );
}