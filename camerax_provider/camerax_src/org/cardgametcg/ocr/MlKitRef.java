package org.cardgametcg.ocr;

// Force ML Kit classes into the DEX so pyjnius can find them at runtime.
// Without explicit Java references, the build system may exclude these classes.
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.TextRecognizer;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;
import com.google.android.gms.tasks.Tasks;

@SuppressWarnings("unused")
public class MlKitRef {
    // Prevent R8/ProGuard from removing these references.
    static final Class<?>[] KEEP = {
        InputImage.class,
        TextRecognition.class,
        TextRecognizer.class,
        TextRecognizerOptions.class,
        Tasks.class,
    };
}
