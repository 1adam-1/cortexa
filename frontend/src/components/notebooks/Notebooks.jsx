import { Button } from '../ui/button.tsx';
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
                                        className="border p-2 rounded-md h-56"
                                        id="fileUpload"
                                    />


                                    <Button>Upload</Button>
                                </div>
                            </DialogContent>
                        </Dialog>
                    </CardFooter>
                </Card>
            </div>
        </div>
    );
}