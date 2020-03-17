from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from src.matrix import *
import numpy as np

#kernels
def construct_kernel_train(A, B, P):
    """
    construct four training kernels: AA^t, ABA^t, APA^t, and APBP^tA^t

    Args:
       A - A matrix
       B - B matrix
       P - P matrix
        
    """
    return [A.dot(A.T), A.dot(B).dot(A.T), A.dot(P).dot(A.T), A.dot(P).dot(B).dot(P.T).dot(A.T)]

def construct_kernel_test(A_train, A_test, B, P):
    """
    construct four testing kernels: A_testA^t, A_testBA^t, A_testPA^t, and A_testPBP^tA^t

    Args:
       A_train - A matrix constructed with training data
       A_test - A matrix constructed with testing datas
       B - B matrix
       P - P matrix
        
    """
    return [A_test.dot(A_train.T), A_test.dot(B).dot(A_train.T), A_test.dot(P.T).dot(A_train.T), A_test.dot(P).dot(B).dot(P.T).dot(A_train.T)]

def compute_metrics(mat):
    """
    output metrics including 'tn', 'fp', 'fn', 'tp', 'acc', 'fnr'

    Args:
       mat - confustion matrix 
        
    """
    return mat + [(mat[0]+mat[3])/sum(mat), mat[2]/(mat[2]+mat[3])]#include confusion matrix and acc, fpr

def train_test_svm(kernel_train, kernel_test, y_train, y_test):
    """
    train and test a kernel 

    Args:
       kernel_train - training kernel
       kernel_test - testing kernel
       y_train - labels for training data
       y_test - labels for testing data
        
    """
    svc = SVC(kernel='precomputed')
    svc.fit(kernel_train, y_train)
    train_pred = svc.predict(kernel_train)
    test_pred = svc.predict(kernel_test)
    train_mat = list(confusion_matrix(y_train, train_pred).ravel())
    test_mat = list(confusion_matrix(y_test, test_pred).ravel())
    return {'train':compute_metrics(train_mat),'test':compute_metrics(test_mat)}

def train_test_kernels(kernels_train, kernels_test, y_train, y_test):
    """
    train and test a list of kernels 

    Args:
       kernel_train - a list of training kernels
       kernel_test - a list of testing kernels
       y_train - labels for training data
       y_test - labels for testing data
        
    """
    train = []
    test = []
    for i in range(4):
        d = train_test_svm(kernels_train[i].todense(), kernels_test[i].todense(), y_train, y_test)
        train.append(d['train'])
        test.append(d['test'])
    train_df = pd.DataFrame(train, columns=['tn', 'fp', 'fn', 'tp', 'acc', 'fnr'], index = np.array(['AA^t', 'ABA^t', 'APA^t', 'APBP^tA^t']))
    test_df = pd.DataFrame(test, columns=['tn', 'fp', 'fn', 'tp', 'acc', 'fnr'], index = np.array(['AA^t', 'ABA^t', 'APA^t', 'APBP^tA^t']))
    train_df.to_csv(os.path.join('output', 'train_result.txt'))
    test_df.to_csv(os.path.join('output', 'test_result.txt'))
    return train_df, test_df

def kernel_models(smalis, y):
    """
    the whole process of constructing matrix, training, and testing kernels 

    Args:
       smalis - dataframe of smali files
       y - labels of data
        
    """
    X_train, X_test, y_train, y_test = train_test_split(smalis, y, test_size=0.33, shuffle=True)
    print('constructing matrices...')
    A, A_test, B, P = construct_matrices(X_train, X_test)
    save_matrix_to_file(A, 'output/A.npz') #save matrices to file
    save_matrix_to_file(B, 'output/B.npz')
    save_matrix_to_file(P, 'output/P.npz')
    save_matrix_to_file(A_test, 'output/A_test.npz')
    print('finish matrices construction and saved to output directory')
    
    print('constructing kernels...')
    kernels_train = construct_kernel_train(A, B, P) #construct kernels
    kernels_test = construct_kernel_test(A, A_test, B, P)
    print('finish kernel construction')
    
    print('start training...')
    train = []
    test = []
    for i in range(4):
        d = train_test_svm(kernels_train[i].todense(), kernels_test[i].todense(), y_train, y_test)
        train.append(d['train'])
        test.append(d['test'])
    print('finish training')
    train_df = pd.DataFrame(train, columns=['tn', 'fp', 'fn', 'tp', 'acc', 'fnr'], index = np.array(['AA^t', 'ABA^t', 'APA^t', 'APBP^tA^t']))
    test_df = pd.DataFrame(test, columns=['tn', 'fp', 'fn', 'tp', 'acc', 'fnr'], index = np.array(['AA^t', 'ABA^t', 'APA^t', 'APBP^tA^t']))
    
    train_df.to_csv(os.path.join('output', 'train_result.csv'))
    test_df.to_csv(os.path.join('output', 'test_result.csv'))
    print('train and test result saved to output directory')