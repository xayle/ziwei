import{i as as,h as R,c as W,d as ns,r as g,o as ls,a as is,b as k,e as s,w as U,f as u,u as o,n as f,g as c,j as rs,v as ds,F as D,k as T,l as ss,t as p,m as cs,p as B,q as I,s as ps,x as v,_ as vs}from"./index-C_Y5Awyv.js";import{u as us}from"./profile-Dowdd6cY.js";import{u as hs}from"./report-BByvuc4J.js";import{C as fs}from"./CityPicker-DCKz8lXh.js";import"./report-DO7DrPoZ.js";import"./client-CuyCQV6X.js";import"./ganzhi-CVUk8nxX.js";/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const es=d=>d==="";/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ks=(...d)=>d.filter((a,n,h)=>!!a&&a.trim()!==""&&h.indexOf(a)===n).join(" ").trim();/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ts=d=>d.replace(/([a-z0-9])([A-Z])/g,"$1-$2").toLowerCase();/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ms=d=>d.replace(/^([A-Z])|[\s-_]+(\w)/g,(a,n,h)=>h?h.toUpperCase():n.toLowerCase());/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const ys=d=>{const a=ms(d);return a.charAt(0).toUpperCase()+a.slice(1)};/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */var $={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const bs=Symbol("lucide-icons");function ws(){return as(bs,{})}/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const gs=({name:d,iconNode:a,absoluteStrokeWidth:n,"absolute-stroke-width":h,strokeWidth:y,"stroke-width":b,size:x,color:N,...z},{slots:w})=>{const{size:_,color:A,strokeWidth:M=2,absoluteStrokeWidth:q=!1,class:j=""}=ws(),S=W(()=>{const C=es(n)||es(h)||n===!0||h===!0||q===!0,i=y||b||M||$["stroke-width"];return C?Number(i)*24/Number(x??_??$.width):i});return R("svg",{...$,...z,width:x??_??$.width,height:x??_??$.height,stroke:N??A??$.stroke,"stroke-width":S.value,class:ks("lucide",j,...d?[`lucide-${ts(ys(d))}-icon`,`lucide-${ts(d)}`]:["lucide-icon"])},[...a.map(C=>R(...C)),...w.default?[w.default()]:[]])};/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const r=(d,a)=>(n,{slots:h,attrs:y})=>R(gs,{...y,...n,iconNode:a,name:d},h.default?{default:h.default}:void 0);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Cs=[["path",{d:"M7 7h10v10",key:"1tivn9"}],["path",{d:"M7 17 17 7",key:"1vkiza"}]],F=r("arrow-up-right",Cs);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const _s=[["path",{d:"M8 2v4",key:"1cmpym"}],["path",{d:"M16 2v4",key:"4m81vk"}],["rect",{width:"18",height:"18",x:"3",y:"4",rx:"2",key:"1hopcy"}],["path",{d:"M3 10h18",key:"8toen8"}],["path",{d:"M8 14h.01",key:"6423bh"}],["path",{d:"M12 14h.01",key:"1etili"}],["path",{d:"M16 14h.01",key:"1gbofw"}],["path",{d:"M8 18h.01",key:"lrp35t"}],["path",{d:"M12 18h.01",key:"mhygvu"}],["path",{d:"M16 18h.01",key:"kzsmim"}]],Ms=r("calendar-days",_s);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const zs=[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["path",{d:"m9 12 2 2 4-4",key:"dzmm74"}]],os=r("circle-check",zs);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const $s=[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["circle",{cx:"12",cy:"12",r:"1",key:"41hilf"}]],O=r("circle-dot",$s);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const xs=[["rect",{width:"8",height:"4",x:"8",y:"2",rx:"1",key:"1oijnt"}],["path",{d:"M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-.5",key:"1but9f"}],["path",{d:"M16 4h2a2 2 0 0 1 1.73 1",key:"1p8n7l"}],["path",{d:"M8 18h1",key:"13wk12"}],["path",{d:"M21.378 12.626a1 1 0 0 0-3.004-3.004l-4.01 4.012a2 2 0 0 0-.506.854l-.837 2.87a.5.5 0 0 0 .62.62l2.87-.837a2 2 0 0 0 .854-.506z",key:"2t3380"}]],Ns=r("clipboard-pen-line",xs);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const As=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",key:"1oefj6"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5",key:"wfsgrz"}],["path",{d:"m9 15 2 2 4-4",key:"1grp1n"}]],qs=r("file-check",As);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ss=[["path",{d:"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z",key:"1oefj6"}],["path",{d:"M14 2v5a1 1 0 0 0 1 1h5",key:"wfsgrz"}],["path",{d:"M10 9H8",key:"b1mrlr"}],["path",{d:"M16 13H8",key:"t4e002"}],["path",{d:"M16 17H8",key:"z1uh3a"}]],Vs=r("file-text",Ss);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Hs=[["path",{d:"m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2",key:"usdka0"}]],Ls=r("folder-open",Hs);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ds=[["path",{d:"M19.414 14.414C21 12.828 22 11.5 22 9.5a5.5 5.5 0 0 0-9.591-3.676.6.6 0 0 1-.818.001A5.5 5.5 0 0 0 2 9.5c0 2.3 1.5 4 3 5.5l5.535 5.362a2 2 0 0 0 2.879.052 2.12 2.12 0 0 0-.004-3 2.124 2.124 0 1 0 3-3 2.124 2.124 0 0 0 3.004 0 2 2 0 0 0 0-2.828l-1.881-1.882a2.41 2.41 0 0 0-3.409 0l-1.71 1.71a2 2 0 0 1-2.828 0 2 2 0 0 1 0-2.828l2.823-2.762",key:"17lmqv"}]],Ts=r("heart-handshake",Ds);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const js=[["path",{d:"M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8",key:"1357e3"}],["path",{d:"M3 3v5h5",key:"1xhq8a"}],["path",{d:"M12 7v5l4 2",key:"1fdv2h"}]],Es=r("history",js);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ps=[["path",{d:"M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z",key:"nnexq3"}],["path",{d:"M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12",key:"mt58a7"}]],Us=r("leaf",Ps);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Bs=[["path",{d:"M14 4.1 12 6",key:"ita8i4"}],["path",{d:"m5.1 8-2.9-.8",key:"1go3kf"}],["path",{d:"m6 12-1.9 2",key:"mnht97"}],["path",{d:"M7.2 2.2 8 5.1",key:"1cfko1"}],["path",{d:"M9.037 9.69a.498.498 0 0 1 .653-.653l11 4.5a.5.5 0 0 1-.074.949l-4.349 1.041a1 1 0 0 0-.74.739l-1.04 4.35a.5.5 0 0 1-.95.074z",key:"s0h3yz"}]],Is=r("mouse-pointer-click",Bs);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Fs=[["path",{d:"M20.341 6.484A10 10 0 0 1 10.266 21.85",key:"1enhxb"}],["path",{d:"M3.659 17.516A10 10 0 0 1 13.74 2.152",key:"1crzgf"}],["circle",{cx:"12",cy:"12",r:"3",key:"1v7zrd"}],["circle",{cx:"19",cy:"5",r:"2",key:"mhkx31"}],["circle",{cx:"5",cy:"19",r:"2",key:"v8kfzx"}]],Os=r("orbit",Fs);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Rs=[["path",{d:"M3 7V5a2 2 0 0 1 2-2h2",key:"aa7l1z"}],["path",{d:"M17 3h2a2 2 0 0 1 2 2v2",key:"4qcy5o"}],["path",{d:"M21 17v2a2 2 0 0 1-2 2h-2",key:"6vwrx8"}],["path",{d:"M7 21H5a2 2 0 0 1-2-2v-2",key:"ioqczr"}],["circle",{cx:"12",cy:"12",r:"3",key:"1v7zrd"}],["path",{d:"m16 16-1.9-1.9",key:"1dq9hf"}]],Ws=r("scan-search",Rs);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Zs=[["path",{d:"M14 17H5",key:"gfn3mx"}],["path",{d:"M19 7h-9",key:"6i9tg"}],["circle",{cx:"17",cy:"17",r:"3",key:"18b49y"}],["circle",{cx:"7",cy:"7",r:"3",key:"dfmy0x"}]],Gs=r("settings-2",Zs);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Xs=[["path",{d:"m21 17-2.156-1.868A.5.5 0 0 0 18 15.5v.5a1 1 0 0 1-1 1h-2a1 1 0 0 1-1-1c0-2.545-3.991-3.97-8.5-4a1 1 0 0 0 0 5c4.153 0 4.745-11.295 5.708-13.5a2.5 2.5 0 1 1 3.31 3.284",key:"y32ogt"}],["path",{d:"M3 21h18",key:"itz85i"}]],Js=r("signature",Xs);/**
 * @license @lucide/vue v1.16.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const Ks=[["path",{d:"M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z",key:"1s2grr"}],["path",{d:"M20 2v4",key:"1rf3ol"}],["path",{d:"M22 4h-4",key:"gwowj6"}],["circle",{cx:"4",cy:"20",r:"2",key:"6kqj1y"}]],Qs=r("sparkles",Ks),Ys={class:"page-nav"},se={class:"pn-brand-icon"},ee={class:"pn-links"},te={id:"home",class:"hero"},oe={class:"hero-content"},ae={class:"hero-badge fade-up"},ne={class:"hero-ctas fade-up-d1"},le={class:"quick-form fade-up-d2"},ie={class:"qf-row"},re={class:"qf-group qf-dt"},de={class:"qf-group"},ce={class:"gender-toggle"},pe={class:"qf-group qf-city"},ve={class:"service-tabs"},ue=["onClick"],he={class:"svc-tab-icon"},fe={class:"qf-actions"},ke={class:"hero-stats fade-up-d2"},me={class:"hero-stat"},ye={class:"hero-stat-n"},be={id:"services",class:"section-wrap"},we={class:"services-grid"},ge={class:"svc-card-inner"},Ce={class:"svc-card-title"},_e={class:"svc-card-desc"},Me={class:"svc-features"},ze=["onClick"],$e={id:"workflow",class:"workflow-section"},xe={class:"section-wrap"},Ne={class:"workflow-steps"},Ae={class:"wf-row"},qe={class:"wf-card wf-card-accent"},Se={class:"wf-icon wf-icon-amber"},Ve={class:"wf-row"},He={class:"wf-card wf-card-left"},Le={class:"wf-icon wf-icon-stone wf-icon-right"},De={class:"wf-row"},Te={class:"wf-card"},je={class:"wf-icon wf-icon-stone"},Ee={class:"wf-row"},Pe={class:"wf-card wf-card-left"},Ue={class:"wf-icon wf-icon-stone wf-icon-right"},Be={id:"cases",class:"section-wrap"},Ie={key:0,class:"cases-grid"},Fe={class:"case-card-top"},Oe={class:"case-name"},Re={class:"case-info-row"},We={class:"case-meta-inline"},Ze={class:"case-city"},Ge={key:0,class:"case-tags"},Xe=["onClick"],Je={key:1,class:"cases-empty"},Ke={id:"reports",class:"section-wrap"},Qe={class:"reports-dark-card"},Ye={class:"reports-dark-inner"},st={class:"reports-left"},et={class:"reports-badge"},tt={class:"reports-actions"},ot={class:"reports-preview"},at={class:"rp-header"},nt={class:"rp-sub"},lt={class:"rp-title"},it={class:"rp-steps"},rt={class:"rp-step rp-current"},dt={id:"tools",class:"section-wrap section-last"},ct={class:"tools-bar"},pt={class:"tools-btns"},vt=ns({__name:"HomeView",setup(d){const a=ps(),n=us(),h=hs(),y=g(null),b=g("home"),x=["home","services","workflow","cases","reports","tools"];function N(){const l=y.value;if(!l)return;const e=l.scrollTop+l.clientHeight*.35;let V="home";for(const H of x){const L=l.querySelector(`#${H}`);L&&L.offsetTop<=e&&(V=H)}b.value=V}const z=g(n.birthDt||"1990-01-15T08:30"),w=g(n.gender==="male"||n.gender==="female"?n.gender:"male"),_=g(n.cityName||"北京"),A=g(n.province||"北京市"),M=g(n.lon),q=g(n.cityName||"北京");function j(l){M.value=l.lon,_.value=l.cityName,A.value=l.province,q.value=l.cityName}const S=[{key:"bazi",label:"四柱八字",desc:"通过出生日期解读命格格局与人生走势。",tabChar:"八",iconComp:Ms,isAmber:!0,route:"/bazi",features:["格局断命","大运流年","用神喜忌","五行强弱"]},{key:"ziwei",label:"紫微斗数",desc:"探索性格特质、时运节点与人生主题宫位。",tabChar:"紫",iconComp:Os,isAmber:!1,route:"/ziwei",features:["宫位排盘","主星解读","大限流年","性格命盘"]},{key:"name",label:"姓名分析",desc:"解析五格架构吉凶，提供改名优化方案。",tabChar:"名",iconComp:Js,isAmber:!1,route:"/name",features:["五格分析","三才配置","笔画吉凶","改名推荐"]},{key:"compat",label:"合婚分析",desc:"匹配双方缘分，评估情感相处节律与忌日。",tabChar:"合",iconComp:Ts,isAmber:!1,route:"/compat",features:["八字合盘","大运对照","忌日禁忌","缘分评分"]}],C=g("bazi"),i=W(()=>h.caseList.slice(0,4)),Z=W(()=>h.caseList.length);function G(l){return l?l.slice(0,10).replaceAll("-","."):"—"}function X(l){return l==="female"?"女命":"男命"}function E(){C.value!=="compat"&&n.setProfile({birthDt:z.value,gender:w.value,cityName:_.value,province:A.value,lon:M.value}),a.push(S.find(l=>l.key===C.value).route)}return ls(()=>{var l;(l=y.value)==null||l.removeEventListener("scroll",N)}),is(()=>{var l;h.loadCaseList(),z.value=n.birthDt||"1990-01-15T08:30",w.value=n.gender==="male"||n.gender==="female"?n.gender:"male",_.value=n.cityName||"北京",A.value=n.province||"北京市",M.value=n.lon,q.value=n.cityName||"北京",(l=y.value)==null||l.addEventListener("scroll",N,{passive:!0}),N()}),(l,e)=>{var V,H,L,J,K,Q,Y;return v(),k("div",{ref_key:"containerRef",ref:y,class:"home-page"},[s("nav",Ys,[s("a",{href:"#home",class:"pn-brand",onClick:e[0]||(e[0]=U(t=>{var m;return(m=y.value)==null?void 0:m.scrollTo({top:0,behavior:"smooth"})},["prevent"]))},[s("span",se,[u(o(Qs),{size:16})]),e[17]||(e[17]=s("span",{class:"pn-brand-text"},[s("span",{class:"pn-brand-name"},"命理工作台"),s("span",{class:"pn-brand-sub"},"咨询工作室")],-1))]),s("div",ee,[s("a",{class:f(["pn-item",{"pn-active":b.value==="home"}]),href:"#home"},"首页",2),s("a",{class:f(["pn-item",{"pn-active":b.value==="services"}]),href:"#services"},"服务",2),s("a",{class:f(["pn-item",{"pn-active":b.value==="workflow"}]),href:"#workflow"},"工作流",2),s("a",{class:f(["pn-item",{"pn-active":b.value==="cases"}]),href:"#cases"},"案例",2),s("a",{class:f(["pn-item",{"pn-active":b.value==="reports"||b.value==="tools"}]),href:"#reports"},"报告",2)]),e[19]||(e[19]=s("div",{class:"pn-sep"},null,-1)),s("button",{class:"pn-btn pn-secondary",onClick:e[1]||(e[1]=t=>o(a).push("/cases"))},"继续工作"),s("button",{class:"pn-btn pn-primary",onClick:E},[e[18]||(e[18]=c("开始服务 ",-1)),u(o(F),{size:14})])]),s("section",te,[e[31]||(e[31]=s("div",{class:"hero-grid-bg"},null,-1)),e[32]||(e[32]=s("div",{class:"hero-blob hero-blob-r"},null,-1)),e[33]||(e[33]=s("div",{class:"hero-blob hero-blob-l"},null,-1)),s("div",oe,[s("div",ae,[u(o(Us),{size:14}),e[20]||(e[20]=c(" 命理咨询工作台 ",-1))]),e[29]||(e[29]=s("h1",{class:"hero-title fade-up"},[c(" 每次咨询，"),s("br",{class:"hero-br"}),c("从这里清晰开始 ")],-1)),e[30]||(e[30]=s("p",{class:"hero-sub fade-up-d1"},[c(" 专为命理师设计的一站式工作流："),s("br"),c(" 选择服务 · 录入信息 · 审阅分析 · 交付报告，让每次咨询都专注、清晰、高效。 ")],-1)),s("div",ne,[s("button",{class:"hero-cta-primary",onClick:E},[e[21]||(e[21]=c(" 开始服务 ",-1)),u(o(F),{size:18})]),s("button",{class:"hero-cta-secondary",onClick:e[2]||(e[2]=t=>o(a).push("/cases"))},[e[22]||(e[22]=c(" 继续工作 ",-1)),u(o(Es),{size:16})])]),s("div",le,[s("div",ie,[s("label",re,[e[23]||(e[23]=s("span",{class:"qf-label"},"出生时间",-1)),rs(s("input",{"onUpdate:modelValue":e[3]||(e[3]=t=>z.value=t),type:"datetime-local",class:"qf-input"},null,512),[[ds,z.value]])]),s("label",de,[e[24]||(e[24]=s("span",{class:"qf-label"},"性别",-1)),s("div",ce,[s("button",{class:f(["gender-btn",{active:w.value==="male"}]),onClick:e[4]||(e[4]=U(t=>w.value="male",["prevent"]))},"男",2),s("button",{class:f(["gender-btn",{active:w.value==="female"}]),onClick:e[5]||(e[5]=U(t=>w.value="female",["prevent"]))},"女",2)])]),s("label",pe,[e[25]||(e[25]=s("span",{class:"qf-label"},"出生城市",-1)),u(fs,{modelValue:M.value,"onUpdate:modelValue":e[6]||(e[6]=t=>M.value=t),"initial-city":q.value,onCityChange:j},null,8,["modelValue","initial-city"])])]),s("div",ve,[(v(),k(D,null,T(S,t=>s("button",{key:t.key,class:f(["svc-tab",{active:C.value===t.key}]),onClick:m=>C.value=t.key},[s("span",he,p(t.tabChar),1),s("span",null,p(t.label),1)],10,ue)),64))]),s("div",fe,[s("button",{class:"btn-start",onClick:E},[...e[26]||(e[26]=[c(" 开始分析 ",-1),s("span",{class:"btn-arrow"},"→",-1)])]),i.value.length?(v(),k("button",{key:0,class:"btn-secondary",onClick:e[7]||(e[7]=t=>o(a).push("/cases"))}," 继续工作 ")):ss("",!0)])]),s("div",ke,[s("div",me,[s("span",ye,p(Z.value>0?Z.value:"—"),1),e[27]||(e[27]=s("span",{class:"hero-stat-l"},"累计案例",-1))]),e[28]||(e[28]=cs('<div class="hero-stat-sep" data-v-d5449bad></div><div class="hero-stat" data-v-d5449bad><span class="hero-stat-n" data-v-d5449bad>4</span><span class="hero-stat-l" data-v-d5449bad>核心服务</span></div><div class="hero-stat-sep" data-v-d5449bad></div><div class="hero-stat" data-v-d5449bad><span class="hero-stat-n" data-v-d5449bad>6+</span><span class="hero-stat-l" data-v-d5449bad>辅助工具</span></div><div class="hero-stat-sep" data-v-d5449bad></div><div class="hero-stat" data-v-d5449bad><span class="hero-stat-n" data-v-d5449bad>15+</span><span class="hero-stat-l" data-v-d5449bad>分析维度</span></div>',6))])])]),s("section",be,[e[34]||(e[34]=s("div",{class:"section-header"},[s("div",null,[s("p",{class:"section-eyebrow"},"从服务开始"),s("h2",{class:"section-title"},"选择占卜类型")]),s("p",{class:"section-desc"},"让第一步决策保持简单。选定符合客户需求的服务，进入引导式工作流程。")],-1)),s("div",we,[(v(),k(D,null,T(S,t=>s("div",{key:t.key,class:"svc-card"},[s("div",ge,[s("span",{class:f(["svc-icon-wrap",t.isAmber?"icon-amber":"icon-stone"])},[(v(),B(I(t.iconComp),{size:24,"stroke-width":1.7}))],2),s("div",null,[s("h3",Ce,p(t.label),1),s("p",_e,p(t.desc),1),s("div",Me,[(v(!0),k(D,null,T(t.features,m=>(v(),k("span",{key:m,class:"svc-feature-tag"},p(m),1))),128))])])]),s("button",{class:"btn-begin",onClick:m=>o(a).push(t.route)},"开始",8,ze)])),64))])]),s("section",$e,[s("div",xe,[e[52]||(e[52]=s("div",{class:"workflow-header"},[s("p",{class:"section-eyebrow"},"唯一需要遵循的路径"),s("h2",{class:"section-title"},"从选服务到交付报告"),s("p",{class:"workflow-sub"},"每次咨询都遵循同一条清晰路径：选服务 · 录入信息 · 审阅分析 · 生成报告。")],-1)),s("div",Ne,[e[51]||(e[51]=s("div",{class:"workflow-line"},null,-1)),s("div",Ae,[e[37]||(e[37]=s("div",{class:"wf-spacer wf-spacer-hidden-sm"},null,-1)),e[38]||(e[38]=s("div",{class:"wf-num-wrap"},[s("span",{class:"wf-num wf-num-accent"},"01")],-1)),s("div",qe,[s("div",Se,[u(o(Is),{size:22,"stroke-width":1.8})]),e[35]||(e[35]=s("h3",{class:"wf-title"},"选择服务",-1)),e[36]||(e[36]=s("p",{class:"wf-desc"},"从服务列表挑选符合客户需求的命理类型，这将决定整个咨询流程的结构与分析维度。",-1))])]),s("div",Ve,[s("div",He,[s("div",Le,[u(o(Ns),{size:22,"stroke-width":1.8})]),e[39]||(e[39]=s("h3",{class:"wf-title"},"填写信息",-1)),e[40]||(e[40]=s("p",{class:"wf-desc"},"准确录入客户的出生日期、时辰与城市，一次填写即可驱动所有分析引擎。",-1))]),e[41]||(e[41]=s("div",{class:"wf-num-wrap"},[s("span",{class:"wf-num"},"02")],-1)),e[42]||(e[42]=s("div",{class:"wf-spacer wf-spacer-hidden-sm"},null,-1))]),s("div",De,[e[45]||(e[45]=s("div",{class:"wf-spacer wf-spacer-hidden-sm"},null,-1)),e[46]||(e[46]=s("div",{class:"wf-num-wrap"},[s("span",{class:"wf-num"},"03")],-1)),s("div",Te,[s("div",je,[u(o(Ws),{size:22,"stroke-width":1.8})]),e[43]||(e[43]=s("h3",{class:"wf-title"},"审阅分析",-1)),e[44]||(e[44]=s("p",{class:"wf-desc"},"逐项查阅解读结果，识别关键洞见，整理可以向客户清晰说明的要点。",-1))])]),s("div",Ee,[s("div",Pe,[s("div",Ue,[u(o(qs),{size:22,"stroke-width":1.8})]),e[47]||(e[47]=s("h3",{class:"wf-title"},"生成报告",-1)),e[48]||(e[48]=s("p",{class:"wf-desc"},"将完整分析一键转化为精美报告书，供客户留存、随时回顾并用于后续跟进咨询。",-1))]),e[49]||(e[49]=s("div",{class:"wf-num-wrap"},[s("span",{class:"wf-num"},"04")],-1)),e[50]||(e[50]=s("div",{class:"wf-spacer wf-spacer-hidden-sm"},null,-1))])])])]),s("section",Be,[e[57]||(e[57]=s("div",{class:"section-header"},[s("div",null,[s("p",{class:"section-eyebrow"},"最近案例"),s("h2",{class:"section-title"},"继续手头的工作")]),s("p",{class:"section-desc"},"随时返回进行中的客户工作，近期案例始终作为辅助保持可见。")],-1)),i.value.length?(v(),k("div",Ie,[(v(!0),k(D,null,T(i.value,t=>{var m;return v(),k("div",{key:t.id,class:"case-card"},[s("div",Fe,[s("span",{class:f(["case-avatar",t.gender==="female"?"avatar-female":"avatar-male"])},p(((m=t.name)==null?void 0:m.charAt(0))??"？"),3),e[53]||(e[53]=s("span",{class:"case-badge"},"进行中",-1))]),s("h3",Oe,p(t.name||"未命名"),1),s("div",Re,[s("span",{class:f(["case-gender-tag",t.gender==="female"?"gender-female":"gender-male"])},p(X(t.gender)),3),s("span",We,p(G(t.birth_dt_local??"")),1)]),s("p",Ze,"📍 "+p(t.city||"未录入城市"),1),t.tags&&t.tags.length?(v(),k("div",Ge,[(v(!0),k(D,null,T(t.tags.slice(0,2),P=>(v(),k("span",{key:P,class:"case-tag"},p(P),1))),128))])):ss("",!0),s("button",{class:"btn-case-action",onClick:P=>o(a).push(`/report/${t.id}`)},"打开报告",8,Xe)])}),128))])):(v(),k("div",Je,[e[54]||(e[54]=s("div",{class:"cases-empty-icon"},"📁",-1)),e[55]||(e[55]=s("p",{class:"cases-empty-title"},"暂无案例记录",-1)),e[56]||(e[56]=s("p",{class:"cases-empty-sub"},"完成首次分析后，案例将自动保存于此，方便随时继续。",-1)),s("button",{class:"btn-begin",onClick:e[8]||(e[8]=t=>o(a).push("/cases"))},"前往案例档案")]))]),s("section",Ke,[s("div",Qe,[s("div",Ye,[s("div",st,[s("div",et,[u(o(Vs),{size:13}),e[58]||(e[58]=c(" 报告中心",-1))]),e[61]||(e[61]=s("h2",{class:"reports-title"},"报告书是命理咨询的最终交付",-1)),e[62]||(e[62]=s("p",{class:"reports-desc"},"分析完成后，生成一份客户可以留存、随时回顾并用于后续跟进的清晰报告书。",-1)),s("div",tt,[s("button",{class:"btn-report-gen",onClick:e[9]||(e[9]=t=>o(a).push(i.value[0]?`/report/${i.value[0].id}`:"/report"))},[e[59]||(e[59]=c(" 生成报告 ",-1)),u(o(F),{size:15})]),s("button",{class:"btn-report-center",onClick:e[10]||(e[10]=t=>o(a).push("/report"))},[e[60]||(e[60]=c(" 打开报告中心 ",-1)),u(o(Ls),{size:15})])])]),s("div",ot,[s("div",at,[s("div",null,[s("p",nt,p(i.value.length?"最近案例 · "+G(i.value[0].updated_at):"最近报告"),1),s("h3",lt,p(((V=i.value[0])==null?void 0:V.name)??"暂无案例"),1)]),s("span",{class:f(["rp-badge",{"badge-female":((H=i.value[0])==null?void 0:H.gender)==="female"}])},p(i.value[0]?X(i.value[0].gender):"草稿"),3)]),s("div",it,[s("div",{class:f(["rp-step",(L=i.value[0])!=null&&L.name?"rp-done":"rp-current"])},[(v(),B(I((J=i.value[0])!=null&&J.name?o(os):o(O)),{size:18,class:"rp-icon"})),e[63]||(e[63]=c(" 客户信息已填写完整 ",-1))],2),s("div",{class:f(["rp-step",(K=i.value[0])!=null&&K.last_snapshot_at?"rp-done":"rp-current"])},[(v(),B(I((Q=i.value[0])!=null&&Q.last_snapshot_at?o(os):o(O)),{size:18,class:"rp-icon"})),c(" 分析已生成"+p((Y=i.value[0])!=null&&Y.last_snapshot_at?"":"（待执行）"),1)],2),s("div",rt,[u(o(O),{size:18,class:"rp-icon"}),e[64]||(e[64]=c(" 待生成最终报告 ",-1))])])])])])]),s("section",dt,[s("div",ct,[e[66]||(e[66]=s("div",null,[s("p",{class:"tools-eyebrow"},"辅助功能"),s("h2",{class:"tools-title"},"更多工具与专家模式不在主路径中")],-1)),s("div",pt,[s("button",{class:"tool-btn",onClick:e[11]||(e[11]=t=>o(a).push("/zeri"))},"🗓️ 吉日择时"),s("button",{class:"tool-btn",onClick:e[12]||(e[12]=t=>o(a).push("/fengshui"))},"🏠 风水八宅"),s("button",{class:"tool-btn",onClick:e[13]||(e[13]=t=>o(a).push("/cases"))},"📁 案例档案"),s("button",{class:"tool-btn",onClick:e[14]||(e[14]=t=>o(a).push("/workbench"))},"🔬 工作台"),s("button",{class:"tool-btn",onClick:e[15]||(e[15]=t=>o(a).push("/glossary"))},"📚 术语词库"),s("button",{class:"tool-btn",onClick:e[16]||(e[16]=t=>o(a).push("/admin"))},[u(o(Gs),{size:14}),e[65]||(e[65]=c(" 专家模式",-1))])])])])],512)}}}),wt=vs(vt,[["__scopeId","data-v-d5449bad"]]);export{wt as default};
