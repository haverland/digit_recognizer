import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
import parameters as params

class MultiSourceDataLoader:
    def __init__(self):
        self.all_images = []
        self.all_labels = []
        self.source_stats = {}
    
    def load_all_sources(self):
        """
        Load and combine all data sources
        """
        print("Loading multiple data sources...")
        print("=" * 50)
        
        for source_config in params.DATA_SOURCES:
            source_name = source_config['name']
            source_type = source_config['type']
            source_path = source_config['path']
            source_weight = source_config.get('weight', 1.0)
            
            print(f"Loading source: {source_name} (type: {source_type})")
            
            if source_type == 'builtin':
                images, labels = self.load_builtin_dataset(source_name)
            elif source_type == 'folder_structure':
                images, labels = self.load_folder_structure(source_path)
            elif source_type == 'label_file':
                images, labels = self.load_label_file_dataset(source_path)
            else:
                print(f"Unknown source type: {source_type}, skipping...")
                continue
            
            if len(images) == 0:
                print(f"  No data loaded from {source_name}, skipping...")
                continue
            
            # Apply sampling weight (undersample if weight < 1.0)
            if source_weight < 1.0 and len(images) > 0:
                sample_size = int(len(images) * source_weight)
                indices = np.random.choice(len(images), sample_size, replace=False)
                images = images[indices]
                labels = labels[indices]
                print(f"  Sampled {sample_size} images (weight: {source_weight})")
            
            # Store source statistics
            self.source_stats[source_name] = {
                'count': len(images),
                'class_distribution': self.get_class_distribution(labels)
            }
            
            # Add to combined dataset
            self.all_images.append(images)
            self.all_labels.append(labels)
            
            print(f"  Loaded {len(images)} images")
            print(f"  Class distribution: {self.source_stats[source_name]['class_distribution']}")
            print("-" * 30)
        
        if len(self.all_images) == 0:
            print("No data sources could be loaded. Using MNIST fallback.")
            return self.load_mnist_fallback()
        
        # Combine all sources
        combined_images = np.concatenate(self.all_images, axis=0)
        combined_labels = np.concatenate(self.all_labels, axis=0)
        
        print(f"\nCombined dataset:")
        print(f"  Total images: {len(combined_images)}")
        print(f"  Sources: {list(self.source_stats.keys())}")
        
        return combined_images, combined_labels
    
    def load_builtin_dataset(self, dataset_name):
        """
        Load built-in datasets
        """
        if dataset_name.lower() == 'mnist':
            import tensorflow as tf
            (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
            
            # Combine train and test
            images = np.concatenate([x_train, x_test])
            labels = np.concatenate([y_train, y_test])
            
            # Convert to proper format
            if not params.USE_GRAYSCALE:
                images = np.stack([images] * 3, axis=-1)
            else:
                images = np.expand_dims(images, axis=-1)
            
            return images, labels
        else:
            print(f"Unknown builtin dataset: {dataset_name}")
            return np.array([]), np.array([])
    
    def load_folder_structure(self, dataset_path):
        """
        Load dataset from folder structure
        """
        if not os.path.exists(dataset_path):
            print(f"  Dataset path not found: {dataset_path}")
            return np.array([]), np.array([])
        
        images = []
        labels = []
        
        for class_label in range(params.NB_CLASSES):
            class_dir = os.path.join(dataset_path, str(class_label))
            
            if not os.path.exists(class_dir):
                print(f"  Class directory not found: {class_dir}")
                continue
                
            for filename in os.listdir(class_dir):
                if any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp']):
                    image_path = os.path.join(class_dir, filename)
                    
                    # Load image
                    image = cv2.imread(image_path)
                    if image is None:
                        continue
                    
                    images.append(image)
                    labels.append(class_label)
        
        return np.array(images), np.array(labels)
    
    def load_label_file_dataset(self, dataset_path):
        """
        Load dataset with label file
        """
        label_file_path = os.path.join(dataset_path, 'labels.txt')
        images_dir = os.path.join(dataset_path, 'images')
        
        if not os.path.exists(label_file_path) or not os.path.exists(images_dir):
            print(f"  Label file or images directory not found in: {dataset_path}")
            return np.array([]), np.array([])
        
        images = []
        labels = []
        
        with open(label_file_path, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 2:
                filename = parts[0]
                label = int(parts[1])
                
                image_path = os.path.join(images_dir, filename)
                if os.path.exists(image_path):
                    image = cv2.imread(image_path)
                    if image is not None:
                        images.append(image)
                        labels.append(label)
        
        return np.array(images), np.array(labels)
    
    def load_mnist_fallback(self):
        """
        Fallback to MNIST if no sources work
        """
        return self.load_builtin_dataset('mnist')
    
    def get_class_distribution(self, labels):
        """
        Get distribution of classes
        """
        distribution = {}
        for i in range(params.NB_CLASSES):
            count = np.sum(labels == i)
            if count > 0:
                distribution[i] = count
        return distribution
    
    def print_detailed_stats(self):
        """
        Print detailed statistics about loaded data
        """
        print("\n" + "=" * 50)
        print("DATA SOURCE STATISTICS")
        print("=" * 50)
        
        for source_name, stats in self.source_stats.items():
            print(f"\nSource: {source_name}")
            print(f"  Total images: {stats['count']}")
            print(f"  Class distribution:")
            for class_id, count in stats['class_distribution'].items():
                print(f"    Class {class_id}: {count} images")
        
        # Combined statistics
        if len(self.all_images) > 0:
            combined_images = np.concatenate(self.all_images, axis=0)
            combined_labels = np.concatenate(self.all_labels, axis=0)
            
            print(f"\nCOMBINED DATASET:")
            print(f"  Total images: {len(combined_images)}")
            print(f"  Class distribution:")
            for i in range(params.NB_CLASSES):
                count = np.sum(combined_labels == i)
                percentage = (count / len(combined_labels)) * 100
                print(f"    Class {i}: {count} images ({percentage:.1f}%)")

def shuffle_dataset(images, labels, seed=params.SHUFFLE_SEED):
    """
    Shuffle images and labels together
    """
    np.random.seed(seed)
    indices = np.random.permutation(len(images))
    return images[indices], labels[indices]

def load_combined_dataset():
    """
    Main function to load all data sources
    """
    loader = MultiSourceDataLoader()
    images, labels = loader.load_all_sources()
    loader.print_detailed_stats()
    
    # Shuffle the combined dataset
    images, labels = shuffle_dataset(images, labels)
    
    return images, labels

def get_data_splits():
    """
    Get train/validation/test splits from combined data sources
    """
    # Load and combine all data sources
    images, labels = load_combined_dataset()
    
    # Use specified percentage of data
    total_samples = len(images)
    training_samples = int(total_samples * params.TRAINING_PERCENTAGE)
    
    # Take the first N samples (already shuffled)
    images = images[:training_samples]
    labels = labels[:training_samples]
    
    print(f"\nUsing {len(images)} samples ({params.TRAINING_PERCENTAGE*100}% of available)")
    
    # Split into train+val and test
    x_train_val, x_test, y_train_val, y_test = train_test_split(
        images, labels, 
        test_size=0.2, 
        random_state=params.SHUFFLE_SEED,
        shuffle=True,
        stratify=labels
    )
    
    # Further split train+val into train and val
    x_train, x_val, y_train, y_val = train_test_split(
        x_train_val, y_train_val, 
        test_size=params.VALIDATION_SPLIT, 
        random_state=params.SHUFFLE_SEED,
        shuffle=True,
        stratify=y_train_val
    )
    
    print(f"\nFinal Data Splits:")
    print(f"  Training: {len(x_train)} samples")
    print(f"  Validation: {len(x_val)} samples")
    print(f"  Test: {len(x_test)} samples")
    
    # Print final class distribution
    print(f"\nFinal Class Distribution:")
    for split_name, x, y in [("Training", x_train, y_train), 
                            ("Validation", x_val, y_val), 
                            ("Test", x_test, y_test)]:
        print(f"  {split_name}:")
        for i in range(params.NB_CLASSES):
            count = np.sum(y == i)
            if count > 0:
                percentage = (count / len(y)) * 100
                print(f"    Class {i}: {count} ({percentage:.1f}%)")
    
    return (x_train, y_train), (x_val, y_val), (x_test, y_test)