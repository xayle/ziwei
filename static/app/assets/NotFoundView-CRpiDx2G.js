import{ab as L,ac as f,l as N,d as $,c as B,a as n,y as c,B as S,b as u,R as z,o as V,_ as W}from"./index-BE03savc.js";/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const w=e=>e==="";/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const E=(...e)=>e.filter((o,t,s)=>!!o&&o.trim()!==""&&s.indexOf(o)===t).join(" ").trim();/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k=e=>e.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase();/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const I=e=>e.replace(/^([A-Z])|[\s-_]+(\w)/g,(o,t,s)=>s?s.toUpperCase():t.toLowerCase());/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const j=e=>{const o=I(e);return o.charAt(0).toUpperCase()+o.slice(1)};/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */var r={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const H=Symbol("lucide-icons");function M(){return L(H,{})}/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const U=({name:e,iconNode:o,absoluteStrokeWidth:t,"absolute-stroke-width":s,strokeWidth:a,"stroke-width":C,size:i,color:v,...b},{slots:p})=>{const{size:l,color:x,strokeWidth:_=2,absoluteStrokeWidth:g=!1,class:y=""}=M(),A=N(()=>{const d=w(t)||w(s)||t===!0||s===!0||g===!0,h=a||C||_||r["stroke-width"];return d?Number(h)*24/Number(i??l??r.width):h});return f("svg",{...r,...b,width:i??l??r.width,height:i??l??r.height,stroke:v??x??r.stroke,"stroke-width":A.value,class:E("lucide",y,...e?[`lucide-${k(j(e))}-icon`,`lucide-${k(e)}`]:["lucide-icon"])},[...o.map(d=>f(...d)),...p.default?[p.default()]:[]])};/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const m=(e,o)=>(t,{slots:s,attrs:a})=>f(U,{...a,...t,iconNode:o,name:e},s.default?{default:s.default}:void 0);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const F=[["path",{d:"m12 19-7-7 7-7",key:"1l729n"}],["path",{d:"M19 12H5",key:"x3x0zl"}]],O=m("arrow-left",F);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const P=[["path",{d:"M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8",key:"5wwlr5"}],["path",{d:"M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",key:"r6nss1"}]],R=m("house",P),T={class:"not-found"},Z={class:"nf-card"},D={class:"nf-actions"},X=$({__name:"NotFoundView",setup(e){return(o,t)=>(V(),B("div",T,[n("div",Z,[t[3]||(t[3]=n("div",{class:"nf-code"},"404",-1)),t[4]||(t[4]=n("h1",{class:"nf-title"},"页面未找到",-1)),t[5]||(t[5]=n("p",{class:"nf-desc"},"您访问的页面不存在或已被移除",-1)),n("div",D,[c(u(z),{to:"/",class:"nf-btn nf-btn-primary"},{default:S(()=>[c(u(R),{size:16}),t[1]||(t[1]=n("span",null,"返回首页",-1))]),_:1}),n("button",{class:"nf-btn nf-btn-ghost",onClick:t[0]||(t[0]=s=>o.$router.go(-1))},[c(u(O),{size:16}),t[2]||(t[2]=n("span",null,"返回上页",-1))])])])]))}}),G=W(X,[["__scopeId","data-v-2325fe8c"]]);export{G as default};
