import scipy.io
import numpy as np

def inspect_mat_file(filepath):
    """
    .mat 파일을 로드하고 그 안에 있는 변수들의 이름과 각 변수의 기본적인 정보를 출력합니다.

    Args:
        filepath (str): .mat 파일의 경로
    """
    try:
        # .mat 파일 로드
        mat_data = scipy.io.loadmat(filepath)
        print(f"Successfully loaded MAT file: {filepath}")
        print("-" * 30)
        print("Variables (Feature Names or Keys) in the MAT file:")
        
        # mat_data는 딕셔너리 형태이며, 키들이 변수명에 해당합니다.
        # 일반적으로 '__header__', '__version__', '__globals__'와 같은 메타데이터 키도 포함될 수 있습니다.
        # 실제 데이터 변수들만 보려면 이들을 제외할 수 있습니다.
        
        data_keys = [key for key in mat_data.keys() if not key.startswith('__')]
        
        if not data_keys:
            print("No data variables found (only metadata or empty file).")
            return

        for key in data_keys:
            variable = mat_data[key]
            variable_shape = variable.shape if hasattr(variable, 'shape') else "N/A (not a NumPy array)"
            variable_type = type(variable)
            
            print(f"\n  Variable Name (Key): {key}")
            print(f"    Type: {variable_type}")
            print(f"    Shape: {variable_shape}")
            
            # 데이터의 일부를 보고 싶다면 (예: NumPy 배열인 경우)
            if isinstance(variable, np.ndarray) and variable.size > 0:
                print(f"    Data (first 5 elements or rows):")
                if variable.ndim == 1: # 1차원 배열
                    print(f"      {variable[:5]}")
                elif variable.ndim > 1: # 다차원 배열 (첫 5행, 모든 열 또는 첫 5열)
                    print(f"      {variable[:5, ...]}") 
                else: # 0차원 배열 (스칼라)
                     print(f"      {variable}")

            # 만약 변수가 MATLAB 구조체(struct)나 셀(cell) 배열이라면, 더 복잡한 처리가 필요할 수 있습니다.
            # scipy.io.loadmat은 MATLAB 구조체를 NumPy의 structured array로, 셀 배열을 NumPy object array로 변환합니다.
            if variable_type == np.ndarray and variable.dtype.names is not None: # Structured array (MATLAB struct)
                print(f"    This is a structured array. Field names: {variable.dtype.names}")
                # 예시: 첫 번째 요소의 필드 값 출력
                if variable.size > 0:
                    print(f"    Example of first element's fields:")
                    for name in variable.dtype.names:
                        try:
                            field_value = variable[0][name]
                            print(f"      Field '{name}': {field_value} (type: {type(field_value)})")
                        except Exception as e:
                            print(f"      Could not access field '{name}': {e}")


        print("-" * 30)

    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
    except Exception as e:
        print(f"An error occurred while trying to read the MAT file: {e}")

if __name__ == '__main__':
    # 여기에 실제 .mat 파일 경로를 입력하세요.
    # 예시: mat_file_path = 'your_data.mat'
    # 만약 논문에서 언급된 6DMG 데이터베이스의 .mat 파일을 가지고 있다면 그 경로를 사용하세요.
    mat_file_path = input("Enter the path to the .mat file: ")
    
    if not mat_file_path:
        print("No file path provided. Exiting.")
    else:
        inspect_mat_file(mat_file_path)