using System.Collections.Generic; // List 사용에 필요
using UnityEngine;


public class RealTimeController : MonoBehaviour
{
    [SerializeField] private SkeletonMapper.Basis skeletonMapper;   // 전체 뼈대의 기준 데이터 Basis?
    [SerializeField] private List<Listener.Basis> listener;         // 뼈대 정보를 받는 대상들? 확인필요

    // Update is called once per frame
    private void Update()
    {
        for (var i = 0; i < listener.Count; i++) listener[i].MoveBoneMap(skeletonMapper.GetBoneMap());
    }
}