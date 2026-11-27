/* Firebase behind the app's storage calls: anonymous sign-in for everyone, Google sign-in for the manager */
import {initializeApp} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {getAuth,onAuthStateChanged,signInAnonymously,GoogleAuthProvider,signInWithPopup,signOut} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import {initializeFirestore,doc,collection,getDoc,getDocs,setDoc,updateDoc,deleteDoc,onSnapshot,query,where,orderBy,limit} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

const X=window.SW_EXT, CFG=window.SW_FB||{};
const fail=()=>{ if(!X.ready){ X.failed=true; X._res(null); } };
try{
  const app=initializeApp(CFG.config), auth=getAuth(app);
  const fs=initializeFirestore(app,{ignoreUndefinedProperties:true});
  const ADMIN=String(CFG.admin||"").toLowerCase();
  const wrapSnap=s=>({id:s.id,exists:s.exists(),data:()=>s.exists()?s.data():undefined,metadata:{fromCache:s.metadata.fromCache,hasPendingWrites:s.metadata.hasPendingWrites}});
  const dref=p=>{ const r=doc(fs,p); return {id:r.id,path:p,
    get:async()=>wrapSnap(await getDoc(r)), set:d=>setDoc(r,d), update:d=>updateDoc(r,d), delete:()=>deleteDoc(r),
    onSnapshot:(next,err)=>onSnapshot(r,{includeMetadataChanges:false},s=>next(wrapSnap(s)),e=>err&&err({code:"unavailable",message:String(e&&e.message)})),
    collection:c=>cref(p+"/"+c)}; };
  const qref=(p,cons)=>({
    where:(f,op,v)=>qref(p,[...cons,where(f,op,v)]), orderBy:(f,d)=>qref(p,[...cons,orderBy(f,d||"asc")]), limit:n=>qref(p,[...cons,limit(n)]),
    get:async()=>{ const q=await getDocs(cons.length?query(collection(fs,p),...cons):collection(fs,p)); const docs=q.docs.map(wrapSnap); return {docs,size:docs.length,empty:!docs.length}; }});
  const cref=p=>Object.assign(qref(p,[]),{path:p, doc:id=>dref(id?p+"/"+id:doc(collection(fs,p)).path)});
  const db={doc:dref,collection:cref};
  let user=null;
  X.uid=()=>user?user.uid:"";
  X.email=()=>user&&!user.isAnonymous?(user.email||""):"";
  X.isGoogle=()=>!!(user&&!user.isAnonymous&&user.emailVerified&&user.providerData.some(p=>p.providerId==="google.com"));
  X.isAdmin=()=>!!(user&&!user.isAnonymous&&user.emailVerified&&ADMIN&&String(user.email||"").toLowerCase()===ADMIN);
  X.signInGoogle=async()=>{ await signInWithPopup(auth,new GoogleAuthProvider()); };
  X.signOutGoogle=async()=>{ await signOut(auth); await signInAnonymously(auth); };
  onAuthStateChanged(auth,u=>{
    if(!u){ signInAnonymously(auth).catch(fail); return; }
    user=u;
    if(!X.ready){ X.ready=true; X._res({db,user:{id:async()=>user?user.uid:null}}); }
    for(const f of X._l){ try{ f(); }catch(e){} }
  });
}catch(e){ console.error(e); fail(); }
