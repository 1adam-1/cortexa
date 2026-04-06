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
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            
            if (response.ok) {
                alert("Fichier envoyé avec succès au RAG !");
                console.log(data);
                setSelectedFile(null);
            } else {
                alert(`Erreur : ${data.error}`);
            }
        } catch (error) {
            console.error("Erreur lors de l'envoi :", error);
            alert("Erreur de connexion avec le serveur.");
        } finally {
            setIsUploading(false);
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
                                        disabled={isUploading || !selectedFile}  
                                    >
                                        {isUploading ? "Uploading..." : "Upload au RAG"}
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