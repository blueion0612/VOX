using System.Collections.Generic;
using System.Linq;
using System.Xml.Linq;
using UnityEngine;

        // 모션 XML 데이터를 파싱하여 bone 구조를 생성해주는 코드

namespace SkeletonMapper
{
    public class Basis : MonoBehaviour
    {
        // the scene model to be moved according to motion capture data
        public GameObject destGameObject;           // 최종 스켈레톤 구조가 붙을 부모 GameObject
        public TextAsset motiveSkeletonXML;         // Motive 프로그램에서 추출된 스켈레톤 정보 XML 파일

        // Lookup map for Motive skeleton bone IDs (keys) and their corresponding GameObjects in Unity (values).
        protected Dictionary<string, GameObject> BoneMap = new();   // Listener가 받을 뼈 이름과 오브젝트 이름 딕셔너리
        protected GameObject RootObj;               // 생성된 전체 스켈레톤 구조의 루트 GameObject

        private string _skeletonName;
        [SerializeField] private bool _posGizmos;   // true일 때 각 오브젝트에 시각화용 큐브를 붙임
        
        /**
        * Parse the input moCapSkeletonXML file and creates a Unity skeleton accordingly.
         * It parses the skeleton name, stored bone IDs, their hierarchy and offsets. The skeleton uses the public
         * _skeletonRootObj as its root object. All bones are also stored in the _boneObjectMap with their ID and GameObject
         * for later lookup.
        */
        private void Start()
        {
            ParseXMLToUnityHierarchy();             // 모션 XML 데이터를 파싱한 후 Unity 안에 뼈 구조를 생성, 뼈끼리 부모-자식 관계로 연결해주는 함수 
        }

        /**
        * This function parses the input moCapSkeletonXML file and creates a Unity skeleton accordingly.
         * It parses the skeleton name, stored bone IDs, their hierarchy and offsets. The skeleton uses the public
         * _skeletonRootObj as its root object. All bones are also stored in the _boneObjectMap with their ID and GameObject
         * for later lookup.
        */
        protected void ParseXMLToUnityHierarchy()
        {
            var moCapSkeleton = XDocument.Parse(motiveSkeletonXML.text);            // XML 텍스트 내용을 XML 문서 객체 MoCapSkeleton으로 만들어준다.

            // Parse skeleton name from XML
            var nameQuery = from c in moCapSkeleton.Root.Descendants("property")    // 모든 property 태그를 대상으로 가져온다.
                where c.Element("name").Value == "NodeName"                         
                select c.Element("value").Value;                                    // NodeName 인 것의 Value 선택
            var skeletonName = nameQuery.First();                                   // skeletonName 에는 첫번째 것만 저장

            // Parse all bones with parents and offsets
            var bonesQuery = from c in moCapSkeleton.Root.Descendants("bone")       // 모든 bone 태그를 대상으로
                select (c.Attribute("id").Value,                                    
                    c.Element("offset").Value.Split(","),
                    c.Element("parent_id").Value);                                  // 뼈 id, offset, 부모 id 를 뽑아 튜플로 만든다. 나중에 뼈 구조 만들고 부모-자식으로 연결

            // create a new object if it doesn't exist yet 
            if (!RootObj)
            {
                RootObj = new GameObject("Generated_" + skeletonName);              // GameObject 생성
                // attach it to the dest game object
                var parentTransform = destGameObject.transform;                     // destGameObject 는 아바타를 의미.
                RootObj.transform.SetPositionAndRotation(
                    parentTransform.position,
                    parentTransform.rotation                                        // 위치, 회전을 그대로 RootObj 에 적용
                );
                RootObj.transform.parent = parentTransform;                         // 완성된 RootObj 를 destGameObject 의 자식으로 붙인다.
            }

            // recreate Motive skeleton structure in Unity
            foreach (var bone in bonesQuery)
            {
                // transform the XML ID to a Mechanim ID for the lookup map
                var mKey = XmlIDtoMecanimID(bone.Item1);

                // create a new object if it doesn't exist yet (might already exist in case we re-parse the XML)
                if (!BoneMap.ContainsKey(mKey))
                {
                    if (_posGizmos)
                    {
                        // show Gizmos only if the flag is true
                        BoneMap[mKey] = GameObject.CreatePrimitive(PrimitiveType.Cube);
                        BoneMap[mKey].name = skeletonName + "_" + mKey;
                        BoneMap[mKey].transform.localScale = new Vector3(0.1f, 0.1f, 0.1f);
                    }
                    else
                    {
                        BoneMap[mKey] = new GameObject(skeletonName + "_" + mKey);
                    }

                }

                // BoneMap[mKey] = new GameObject(skeletonName + "_" + mKey);
                //the bone with parent 0 is the root object
                BoneMap[mKey].transform.parent = bone.Item3 == "0"
                    ? RootObj.transform
                    : BoneMap[XmlIDtoMecanimID(bone.Item3)].transform;
                // apply the parsed offsets
                BoneMap[mKey].transform.localPosition = new Vector3(
                    float.Parse(bone.Item2[0]),
                    float.Parse(bone.Item2[1]),
                    float.Parse(bone.Item2[2]));
            }
        }

        /**
         * IDs in the XML of Motive are distinct from the XML or Mechanim IDs.
         * Use this to map from CSV ID to Unity Mechanim ID.
         */
        public static string XmlIDtoMecanimID(string xmlId)
        {
            var dict = new Dictionary<string, string>()
            {
                { "1", "Hips" },
                { "2", "Spine" },
                { "3", "Chest" },
                { "4", "Neck" },
                { "5", "Head" },

                { "6", "LeftShoulder" },
                { "7", "LeftUpperArm" },
                { "8", "LeftLowerArm" },
                { "9", "LeftHand" },

                { "10", "RightShoulder" },
                { "11", "RightUpperArm" },
                { "12", "RightLowerArm" },
                { "13", "RightHand" },

                { "14", "LeftUpperLeg" },
                { "15", "LeftLowerLeg" },
                { "16", "LeftFoot" },
                { "17", "LeftToes" },

                { "18", "RightUpperLeg" },
                { "19", "RightLowerLeg" },
                { "20", "RightFoot" },
                { "21", "RightToes" }
            };
            return dict[xmlId];
        }

        public Dictionary<string, GameObject> GetBoneMap()
        {
            return BoneMap;
        }
    }
}