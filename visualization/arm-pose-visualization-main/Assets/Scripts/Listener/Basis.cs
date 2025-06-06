using System.Collections.Generic;
using UnityEngine;

namespace Listener
{
    public abstract class Basis : MonoBehaviour
    {
        public abstract void MoveBoneMap(Dictionary<string, GameObject> boneMap);   // 딕셔너리 값을 파라미터로 받음. 뼈 이름과 오브젝트의 boneMap.
    }
}