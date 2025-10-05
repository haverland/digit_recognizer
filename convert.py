import tensorflow as tf
import numpy as np
import os
from utils.dataset import load_digit_dataset
from utils.preprocess import preprocess_images
import parameters as params

def representative_dataset():
    """Generate representative dataset for quantization"""
    (x_train, _), _ = load_digit_dataset()
    x_train = preprocess_images(x_train)
    
    for i in range(min(100, len(x_train))):
        yield [x_train[i:i+1]]

def convert_to_tflite_micro():
    """Convert model to TFLite for ESP-DL"""
    
    model_path = os.path.join(params.OUTPUT_DIR, f"{params.MODEL_FILENAME}.h5")
    output_path = os.path.join(params.OUTPUT_DIR, params.TFLITE_FILENAME)
    
    # Load model
    print(f"Loading model from: {model_path}")
    model = tf.keras.models.load_model(model_path)
    
    if params.QUANTIZE_MODEL:
        # Convert to TFLite with int8 quantization
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
        # ESP-DL optimized settings
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = representative_dataset
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        converter.allow_custom_ops = False
        
        print("Converting with INT8 quantization...")
    else:
        # Convert without quantization
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        print("Converting without quantization...")
    
    # Convert
    tflite_model = converter.convert()
    
    # Save
    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    
    # Print model info
    model_size_kb = len(tflite_model) / 1024
    print(f"TFLite model saved: {output_path}")
    print(f"Model size: {model_size_kb:.1f} KB")
    print(f"Input shape: {params.INPUT_SHAPE}")
    print(f"Quantized: {params.QUANTIZE_MODEL}")
    
    return tflite_model

if __name__ == "__main__":
    convert_to_tflite_micro()