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
  addEventListener(k,fn) { this.listeners[k]=fn; }
  focus() {}
}
function setup(query='') {
  const links=[new Element(a+'.html','Alpha'),new Element(b+'.html','Beta'),
    new Element(a+'.html#'+one,'Overload (1)'),new Element(a+'.html#'+two,'Overload (2)'),
    new Element(b+'.html#'+other,'Other')];
  const controls=new Element(), sidebar=new Element(), search=new Element(), clear=new Element();
  const list={tagName:'UL',querySelectorAll:()=>links.slice(0,2)};
  const heading={nextElementSibling:list};sidebar.querySelectorAll=()=>links;
  const location={href:base+'index.html'+query,origin:'https://docs.invalid'};
  const calls=[], replacements=[]; let frameHref='about:blank', inaccessible=false;
  const nativeDocument=new Element();
  const frame=new Element();frame.name='document-content';frame.contentDocument=nativeDocument;
  frame.contentWindow={addEventListener(){},location:{get href(){if(inaccessible)throw Error('cross-origin');return frameHref;},
    replace(url){replacements.push(url);}}};
  const history={pushState(s,_,url){calls.push(['push',s,String(url)]);location.href=String(url);},
    replaceState(s,_,url){calls.push(['replace',s,String(url)]);location.href=String(url);}};
  const window=new Element();
  const nodes={'package-navigation':controls,'compilation-units':heading,'package-search':search,
    'package-results':new Element(),'package-clear':clear};
  const document={getElementById:k=>nodes[k],querySelector:k=>k==='.side-navigation'?sidebar:frame};
  vm.runInNewContext(fs.readFileSync(asset,'utf8'),{document,location,history,window,URL});
  function click(link,inner=false) {
    let prevented=false;
    (inner?nativeDocument:sidebar).listeners.click({target:link,button:0,preventDefault(){prevented=true;}});
    return prevented;
  }
  function complete(url) { frameHref=url;inaccessible=false;frame.listeners.load(); }
  function pop(query) {location.href=base+'index.html'+query;window.listeners.popstate();}
  function state(pkg,decl='') {
    assert.equal(new URL(location.href).searchParams.get('package'),pkg);
    assert.equal(new URL(location.href).searchParams.get('declaration'),decl||null);
    assert.equal(replacements.at(-1),base+(pkg==='Alpha'?a:b)+'.html'+(decl?'#'+decl:''));
  }
  complete(replacements.at(-1));
  return {links,calls,replacements,location,click,complete,pop,state,frame,search,clear,
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
} else {throw Error('Unknown scenario '+scenario);}
console.log(scenario+' pass');