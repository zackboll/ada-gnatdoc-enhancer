/* Small DOM/event double: executes the shipped asset, no router reimplementation.
 * Frame completions are explicitly ordered by tests, never timer-dependent. */
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const asset = process.argv[2], scenario = process.argv[3];
const a='a'.repeat(64), b='b'.repeat(64), one='1'.repeat(64), two='2'.repeat(64), other='3'.repeat(64);
const base='https://docs.invalid/api/';
class Element {
  constructor(href='', text='') {
    this.attrs={href};this.textContent=text;this.target='document-content';
    this.parentElement={hidden:false};this.listeners={};this.dataset={};this.value='';
  }
  getAttribute(k) { return this.attrs[k] ?? null; }
  setAttribute(k,v) { this.attrs[k]=v; }
  removeAttribute(k) { delete this.attrs[k]; }
  closest() { return this; }
  addEventListener(k,fn) {
    this.listenerCounts ??= {};this.listenerCounts[k]=(this.listenerCounts[k] || 0)+1;
    const previous=this.listeners[k];
    this.listeners[k]=previous ? ev => {previous(ev);fn(ev);} : fn;
  }
  focus() {}
}
function setup(query='', initial='about:blank') {
  const links=[new Element(a+'.html','Alpha'),new Element(b+'.html','Beta'),
    new Element(a+'.html#'+one,'Overload (1)'),new Element(a+'.html#'+two,'Overload (2)'),
    new Element(b+'.html#'+other,'Other')];
  const controls=new Element(), sidebar=new Element(), search=new Element(), clear=new Element();
  const list={tagName:'UL',querySelectorAll:()=>links.slice(0,2)};
  const heading={nextElementSibling:list};sidebar.querySelectorAll=()=>links;
  const location={href:base+'index.html'+query,origin:'https://docs.invalid'};
  const calls=[], replacements=[], scrolls=[], callbacks=[]; let frameHref=initial, inaccessible=false, scrollY=9000;
  const nativeDocument=new Element();
  nativeDocument.readyState='complete';
  Object.defineProperty(nativeDocument,'URL',{configurable:true,get(){return frameHref;}});
  const targets=new Map([one,two,other].map(id=>[id,{scrollIntoView(options){
    assert.equal(options.block,'start');scrollY=0;scrolls.push({id,url:frameHref});
  }}]));
  nativeDocument.getElementById=id=>targets.get(id);
  const frame=new Element();frame.name='document-content';frame.contentDocument=nativeDocument;
  const frameWindow=new Element();
  frameWindow.location={get href(){if(inaccessible)throw Error('cross-origin');return frameHref;},
    replace(url){replacements.push(url);}};
  frame.contentWindow=frameWindow;
  const history={pushState(s,_,url){calls.push(['push',s,String(url)]);location.href=String(url);},
    replaceState(s,_,url){calls.push(['replace',s,String(url)]);location.href=String(url);}};
  const window=new Element();
  const nodes={'package-navigation':controls,'compilation-units':heading,'package-search':search,
    'package-results':new Element(),'package-clear':clear};
  const document={getElementById:k=>nodes[k],querySelector:k=>k==='.side-navigation'?sidebar:frame};
  function initialize() {
    vm.runInNewContext(fs.readFileSync(asset,'utf8'),{document,location,history,window,URL,
      requestAnimationFrame(fn){callbacks.push(fn);}});
  }
  initialize();
  function click(link,inner=false) {
    let prevented=false;
    (inner?nativeDocument:sidebar).listeners.click({target:link,button:0,preventDefault(){prevented=true;}});
    return prevented;
  }
  function complete(url) { frameHref=url;inaccessible=false;frame.listeners.load(); }
  function hash(url) { frameHref=url;frameWindow.listeners.hashchange(); }
  function flush() {
    const batch=callbacks.splice(0);assert(batch.length<=16,'unbounded animation callbacks');
    for (const fn of batch) fn();
    assert.equal(callbacks.length,0,'reveal must not retry or poll');
  }
  function pop(query) {location.href=base+'index.html'+query;window.listeners.popstate();}
  function state(pkg,decl='') {
    assert.equal(new URL(location.href).searchParams.get('package'),pkg);
    assert.equal(new URL(location.href).searchParams.get('declaration'),decl||null);
    assert.equal(replacements.at(-1),base+(pkg==='Alpha'?a:b)+'.html'+(decl?'#'+decl:''));
  }
  if (replacements.length) complete(replacements.at(-1));
  return {links,calls,replacements,location,click,complete,pop,state,frame,search,clear,
    scrolls,callbacks,flush,hash,nativeDocument,targets,window,frameWindow,sidebar,initialize,
    pageshow(){window.listeners.pageshow?.({persisted:true});},
    move(){scrollY=9000;},get scrollY(){return scrollY;},
    cross(){inaccessible=true;frame.listeners.load();}};
}
const queries={
  package:'?package=Beta',deep:'?package=Alpha&declaration='+one,
  unknown_package:'?package=Not.Owned&declaration='+one,
  unknown_declaration:'?package=Alpha&declaration='+'f'.repeat(64),
  wrong_package:'?package=Alpha&declaration='+other,
  duplicate_package:'?package=Beta&package=Alpha',
  duplicate_declaration:'?package=Alpha&declaration='+one+'&declaration='+two,
  malformed:'?package=Alpha&declaration=%ZZ',
  injection:'?package=%3Cscript%3E&declaration=javascript%3Aalert(1)',
  malformed_fragment:'?package=Alpha&declaration=%23'+one,
};
if (scenario in queries) {
  const t=setup(queries[scenario]);
  t.state(scenario==='package'?'Beta':'Alpha',scenario==='deep'?one:'');
  assert.equal(t.calls.filter(c=>c[0]==='push').length,0);
  assert.equal(new URL(t.location.href).search,scenario==='package'?'?package=Beta':
    '?package=Alpha'+(scenario==='deep'?'&declaration='+one:''));
} else if (scenario==='history') {
  const t=setup();t.click(t.links[2]);t.complete(base+a+'.html#'+one);
  t.click(t.links[3]);t.complete(base+a+'.html#'+two);t.state('Alpha',two);
  const n=t.calls.length;
  for(let i=0;i<4;i++) {
    t.pop('?package=Alpha&declaration='+one);t.complete(base+a+'.html#'+one);t.state('Alpha',one);
    t.pop('?package=Alpha&declaration='+two);t.complete(base+a+'.html#'+two);t.state('Alpha',two);
  }
  assert.equal(t.calls.length,n);
  assert.equal(t.calls.filter(c=>c[0]==='push').length,2);
  assert.equal(t.links[3].getAttribute('aria-current'),'location');
} else if (scenario==='same_selection') {
  const t=setup();t.click(t.links[0]);assert.equal(t.calls.filter(c=>c[0]==='push').length,0);
  t.click(t.links[2]);t.complete(base+a+'.html#'+one);t.click(t.links[2]);
  assert.equal(t.calls.filter(c=>c[0]==='push').length,1);
} else if (scenario==='stale_load') {
  const t=setup();t.click(t.links[2]);t.click(t.links[4]);
  t.complete(base+a+'.html#'+one);t.state('Beta',other);
  t.pop('?package=Alpha&declaration='+two);
  t.complete(base+b+'.html#'+other);t.state('Alpha',two);
  t.complete(base+a+'.html#'+two);t.state('Alpha',two);
  // Even a completion delivered AFTER the newer navigation acknowledges must
  // not leave the iframe at the superseded target.
  t.complete(base+a+'.html#'+one);t.state('Alpha',two);
  t.complete(base+a+'.html#'+two);t.state('Alpha',two);
  assert.equal(t.calls.filter(c=>c[0]==='push').length,2);
} else if (scenario==='invalid_pop') {
  const t=setup();const n=t.calls.length;t.pop('?package=Beta&declaration='+one);
  // Restoration must not rewrite history, including invalid historical URLs.
  assert.equal(t.replacements.at(-1),base+b+'.html');
  assert.equal(t.links[1].getAttribute('aria-current'),'page');
  assert.equal(t.calls.length,n);
} else if (scenario==='external_frame') {
  const t=setup();const n=t.calls.length;t.cross();assert.equal(t.calls.length,n);t.click(t.links[4]);t.state('Beta',other);
} else if (scenario==='unqualified_frame') {
  const t=setup();const n=t.calls.length;t.complete(base+'arbitrary.html#'+one);
  assert.equal(t.calls.length,n);assert.equal(new URL(t.location.href).search,'?package=Alpha');
} else if (scenario==='native_click') {
  const t=setup();assert(t.click(new Element('#'+two),true));t.state('Alpha',two);
  assert.equal(t.calls.filter(c=>c[0]==='push').length,1);
} else if (scenario==='search') {
  const t=setup();t.search.value='Overload';t.search.listeners.input();
  assert(t.links[4].parentElement.hidden);t.clear.listeners.click();
  assert.equal(t.search.value,'');assert(!t.links[4].parentElement.hidden);
} else if (scenario==='outer_fragment') {
  const t=setup('?package=Alpha#tagged-types');t.click(t.links[2]);
  assert.equal(new URL(t.location.href).hash,'#tagged-types');
} else if (scenario==='bad_links') {
  for (const href of ['https://evil.invalid/'+a+'.html#'+one,'javascript:alert(1)',
    'data:text/html,<h1>bad</h1>','../'+a+'.html#'+one,base+a+'.html#'+one,
    a+'.html#'+other,'arbitrary.html#'+one,'//evil.invalid/'+a+'.html']) {
    const t=setup();t.links[2].attrs.href=href;assert(t.click(t.links[2]));
    assert.equal(t.calls.filter(c=>c[0]==='push').length,0);
    const injected=new Element(href);assert(t.click(injected));
  }
} else if (scenario==='restore_same_url') {
  const t=setup('?package=Alpha&declaration='+one);t.flush();t.move();
  const n=t.replacements.length,h=t.calls.length;
  t.pop('?package=Alpha&declaration='+one);assert.equal(t.scrollY,9000);t.flush();
  assert.equal(t.scrollY,0);assert.equal(t.scrolls.at(-1).id,one);
  assert.equal(t.replacements.length,n);assert.equal(t.calls.length,h);
} else if (scenario==='restore_pageshow') {
  const t=setup('?package=Alpha&declaration='+one);t.flush();t.move();
  const n=t.replacements.length,h=t.calls.length;t.pageshow();t.flush();
  assert.equal(t.scrollY,0);assert.equal(t.replacements.length,n);assert.equal(t.calls.length,h);
} else if (scenario==='reveal_load') {
  const t=setup();t.click(t.links[2]);t.flush();assert.equal(t.scrolls.length,0);
  t.complete(base+a+'.html#'+one);assert.equal(t.scrolls.length,0);t.flush();
  assert.equal(t.scrolls.length,1);assert.equal(t.scrolls[0].id,one);
} else if (scenario==='reveal_hash') {
  const t=setup();t.click(t.links[2]);t.hash(base+a+'.html#'+one);t.flush();
  assert.equal(t.scrolls.length,1);assert.equal(t.scrolls[0].id,one);
  t.move();t.hash(base+a+'.html#'+one);t.flush();
  assert.equal(t.scrollY,9000,'unrequested hash event must not reset user scroll');
} else if (scenario==='reveal_stale_load') {
  const t=setup();t.click(t.links[2]);t.click(t.links[4]);
  t.complete(base+a+'.html#'+one);t.flush();assert.equal(t.scrolls.length,0);
  t.complete(base+b+'.html#'+other);t.flush();assert.equal(t.scrolls.length,1);
  assert.equal(t.scrolls[0].id,other);
} else if (scenario==='deferred_selection') {
  const t=setup();t.click(t.links[2]);t.complete(base+a+'.html#'+one);
  assert.equal(t.callbacks.length,1);t.click(t.links[4]);t.flush();
  assert.equal(t.scrolls.length,0,'superseded callback scrolled A while B pending');
  t.complete(base+b+'.html#'+other);t.flush();assert.equal(t.scrolls[0].id,other);
} else if (scenario==='deferred_round_trip') {
  const t=setup();t.click(t.links[2]);t.complete(base+a+'.html#'+one);
  t.click(t.links[4]);t.click(t.links[2]);assert.equal(t.callbacks.length,2);
  const old=t.callbacks.shift();old();assert.equal(t.scrolls.length,0,'old A callback survived A -> B -> A');
  t.flush();assert.equal(t.scrolls.length,1);
} else if (scenario==='deferred_document') {
  const t=setup();t.click(t.links[2]);t.complete(base+a+'.html#'+one);
  t.frame.contentDocument={readyState:'complete',URL:base+a+'.html#'+one,getElementById(){throw Error('wrong document');}};
  t.flush();assert.equal(t.scrolls.length,0);
} else if (scenario==='incomplete_document') {
  const t=setup();t.nativeDocument.readyState='loading';t.click(t.links[2]);
  t.complete(base+a+'.html#'+one);t.flush();assert.equal(t.scrolls.length,0);
  t.nativeDocument.readyState='complete';t.complete(base+a+'.html#'+one);t.flush();
  assert.equal(t.scrolls.length,1);
} else if (scenario==='wrong_document_url') {
  const t=setup();t.click(t.links[2]);t.complete(base+a+'.html#'+one);
  Object.defineProperty(t.nativeDocument,'URL',{value:base+b+'.html#'+one});
  t.flush();assert.equal(t.scrolls.length,0);
} else if (scenario==='missing_target') {
  const t=setup();t.targets.delete(one);t.click(t.links[2]);t.complete(base+a+'.html#'+one);
  t.flush();assert.equal(t.scrolls.length,0);
} else if (scenario==='invalid_reveal') {
  for (const query of ['?package=Alpha','?package=Alpha&declaration=',
    '?package=Alpha&declaration='+other,'?package=Alpha&declaration='+'f'.repeat(64),
    '?package=Alpha&declaration='+one+'&declaration='+two,'?package=Alpha&declaration=%ZZ',
    '?package=Beta&package=Alpha&declaration='+one]) {
    const t=setup(query);t.flush();t.pageshow();t.flush();
    assert.equal(t.scrolls.length,0);assert.equal(t.callbacks.length,0);
  }
} else if (scenario==='foreign_reveal') {
  const t=setup();t.click(t.links[2]);t.complete(base+a+'.html#'+one);t.cross();t.flush();
  assert.equal(t.scrolls.length,0);t.complete(base+a+'.html#'+one);t.flush();assert.equal(t.scrolls.length,1);
} else if (scenario==='repeated_visible_history') {
  const t=setup();t.click(t.links[2]);t.complete(base+a+'.html#'+one);t.flush();
  t.click(t.links[3]);t.hash(base+a+'.html#'+two);t.flush();const n=t.calls.length;
  for(let i=0;i<8;i++) for(const id of [one,two]) {
    t.move();t.pop('?package=Alpha&declaration='+id);t.hash(base+a+'.html#'+id);t.flush();
    assert.equal(t.scrollY,0);assert.equal(t.scrolls.at(-1).id,id);
  }
  assert.equal(t.calls.length,n);assert.equal(t.calls.filter(c=>c[0]==='push').length,2);
} else if (scenario==='already_loaded_initial') {
  const t=setup('?package=Alpha&declaration='+one,base+a+'.html#'+one);t.flush();
  assert.equal(t.replacements.length,0);assert.equal(t.scrolls.length,1);
  assert(t.click(new Element('#'+two),true));t.hash(base+a+'.html#'+two);t.flush();
  assert.equal(t.scrolls.at(-1).id,two);
} else if (scenario==='listeners_bounded') {
  const t=setup();const h=t.calls.length;
  for(let i=0;i<8;i++){t.initialize();t.complete(base+a+'.html');t.pageshow();t.flush();}
  assert.equal(t.nativeDocument.listenerCounts.click,1);assert.equal(t.frameWindow.listenerCounts.hashchange,1);
  assert.equal(t.frame.listenerCounts.load,1);assert.equal(t.sidebar.listenerCounts.click,1);
  assert.equal(t.window.listenerCounts.popstate,1);assert.equal(t.window.listenerCounts.pageshow,1);
  assert.equal(t.calls.length,h);
} else if (scenario==='user_scroll_preserved') {
  const t=setup('?package=Alpha&declaration='+one);t.flush();t.move();t.flush();
  t.search.value='Overload';t.search.listeners.input();t.flush();assert.equal(t.scrollY,9000);
  assert(!t.window.listeners.scroll);assert(!t.frameWindow.listeners.scroll);
} else if (scenario==='query_compatibility') {
  const t=setup('?unrelated=kept&package=Alpha#tagged-types');t.click(t.links[2]);
  t.complete(base+a+'.html#'+one);t.flush();const n=t.calls.length;
  t.pageshow();t.flush();assert.equal(t.calls.length,n);
  assert.equal(new URL(t.location.href).searchParams.get('unrelated'),'kept');
  assert.equal(new URL(t.location.href).hash,'#tagged-types');
} else {throw Error('Unknown scenario '+scenario);}
console.log(scenario+' pass');