"""Actual record aggregates and every entry in the new progress dashboard."""
import csv
import io
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = 'http://127.0.0.1:8000/'
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1672, 'height': 945}, accept_downloads=True)
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    saved = lambda: page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')

    def dashboard():
        page.goto(BASE + '#records')
        page.locator('.progress-dashboard').wait_for()

    def back():
        page.locator('.practice-back').click()
        page.wait_for_function('!document.querySelector("#lesson-dialog").open')

    dashboard()
    expect(page.locator('.progress-page-heading h1')).to_have_text('学习进度')
    assert page.locator('.progress-metric').count() == 4
    assert page.locator('.progress-category-row').count() == 8
    assert page.locator('.progress-chart-bar').count() == 7
    assert page.locator('[data-progress-today-time]').inner_text() == '0分钟'
    assert page.locator('[data-progress-total-words]').inner_text() == '0个'
    assert '还没有学习记录' in page.locator('.progress-records').inner_text()
    assert 'NaN' not in page.locator('#content').inner_text()
    page.locator('[data-progress-trend="checkin"]').click()
    assert [b.get_attribute('data-value') for b in page.locator('.progress-chart-bar').all()] == ['0'] * 7
    page.locator('.progress-chart-bar').first.click()
    expect(page.locator('#progress-day-dialog')).to_be_visible()
    assert '当天暂无' in page.locator('#progress-day-dialog').inner_text()
    page.locator('#progress-day-dialog [data-close]').click()
    print('PASS: fresh dashboard has actual zero counts, all categories, seven empty days and usable empty-day details', flush=True)

    dates = page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key)),ids=s.words.map(w=>w.id),dates=[];s.days={};
      for(let i=0;i<7;i++){const d=new Date();d.setDate(d.getDate()-6+i);const date=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');dates.push(date);s.days[date]={seconds:[15,28,12,20,35,18,9][i]*60,words:ids.slice(0,[20,25,16,28,52,36,24][i]),sentences:i===3?['old-sentence']:[],mistakes:i===3?2:0,checked:i>=3&&i<=5};}
      s.days[dates[0]].words.push('old-word:historic');
      for(let i=7;i<27;i++){const d=new Date();d.setDate(d.getDate()-i);const date=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');s.days[date]={seconds:60,words:[ids[0]],sentences:[],mistakes:0,checked:false};}
      s.wordStatus={};ids.slice(0,22).forEach(id=>s.wordStatus[id]='mastered');s.wordStatus[ids[3]]='unfamiliar';s.wordStatus[ids[135]]='mastered';s.plan.minutes=20;s.plan.words=50;
      s.practiceResume={ids:ids.slice(0,22),wordId:ids[3],answered:false,finished:false};
      s.notes=[{id:'progress-note',title:'原有手账',body:'保留学习记录',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];
      s.challenges=[{id:'old-challenge',createdAt:'2026-10-01T00:00:00Z',correct:8,answered:10,score:80}];localStorage.setItem(key,JSON.stringify(s));return dates;}''')
    page.reload()
    baseline = saved()
    expect(page.locator('[data-progress-today-time]')).to_have_text('9分钟')
    expect(page.locator('[data-progress-today-words]')).to_have_text('24个')
    expect(page.locator('[data-progress-streak]')).to_have_text('3天')
    expect(page.locator('[data-progress-total-words]')).to_have_text('54个')
    assert page.get_by_role('progressbar', name='今日时长完成度', exact=True).get_attribute('aria-valuenow') == '45'
    assert page.get_by_role('progressbar', name='今日单词完成度', exact=True).get_attribute('aria-valuenow') == '48'
    assert '11 分钟' in page.locator('.progress-goal-hint').inner_text()
    assert '26 个单词' in page.locator('.progress-goal-hint').inner_text()
    assert page.locator('[data-progress-category="C01"] .progress-category-count').inner_text() == '22 / 136'
    assert page.locator('[data-progress-category="C02"] .progress-category-count').inner_text() == '0 / 220'
    assert [float(b.get_attribute('data-value')) for b in page.locator('.progress-chart-bar').all()] == [15, 28, 12, 20, 35, 18, 9]
    page.screenshot(path='/tmp/learning-progress-v24.png', full_page=True)
    page.locator('[data-progress-trend="words"]').click()
    assert [int(b.get_attribute('data-value')) for b in page.locator('.progress-chart-bar').all()] == [21, 25, 16, 28, 52, 36, 24]
    assert page.locator('[data-progress-trend="words"]').get_attribute('aria-pressed') == 'true'
    page.locator('[data-progress-trend="checkin"]').click()
    assert [int(b.get_attribute('data-value')) for b in page.locator('.progress-chart-bar').all()] == [0, 0, 0, 1, 1, 1, 0]
    assert '未打卡' in page.locator(f'.progress-records [data-progress-date="{dates[-1]}"]').inner_text()
    page.locator(f'.progress-chart-bar[data-day="{dates[3]}"]').click()
    expect(page.locator('#progress-day-title')).to_contain_text(dates[3])
    assert page.locator('.progress-day-words span').count() == 28
    assert '答错记录 2 次' in page.locator('#progress-day-dialog').inner_text()
    page.locator('#progress-day-dialog [data-close]').click()
    assert saved() == baseline
    print('PASS: real daily goals, duplicate-free lifetime words, streak, categories, all trend switches and read-only day details', flush=True)

    page.locator('.progress-records [data-route="records/history"]').click()
    expect(page.locator('.progress-page-heading h1')).to_have_text('全部学习记录')
    assert page.locator('.progress-record-table tbody tr').count() == 20
    assert page.locator('.progress-record-table tbody tr').first.get_attribute('data-progress-date') == dates[-1]
    page.locator('.progress-pagination [data-route="records/history/2"]').click()
    expect(page.locator('.progress-record-table tbody tr')).to_have_count(7)
    page.reload()
    expect(page.locator('.progress-record-table tbody tr')).to_have_count(7)
    with page.expect_download() as dl:
        page.locator('[data-action="export-progress"]').click()
    path = Path('/tmp/learning-progress.csv')
    dl.value.save_as(path)
    exported = list(csv.reader(io.StringIO(path.read_text(encoding='utf-8-sig'))))
    assert len(exported) == 28
    assert exported[1] == [dates[-1], '540', '24', '0', '未打卡']
    page.locator('.progress-legacy>summary').click()
    assert '80 分' in page.locator('.progress-legacy').inner_text() or '80' in page.locator('.progress-legacy').inner_text()
    page.locator('.progress-history-toolbar [data-route="records"]').click()
    page.locator('.progress-dashboard').wait_for()
    for i in range(1, 9):
        page.locator(f'[data-progress-category="C{i:02}"]').click()
        expect(page.locator('.mvp-subcategory')).to_have_count(4)
        assert page.url.endswith(f'#words/C{i:02}')
        dashboard()
    print('PASS: all history, paging and reload, actual CSV download, preserved rankings/challenges and eight category routes', flush=True)

    page.locator('.progress-goals [data-route="plan"]').click()
    page.locator('#plan-minutes').fill('25')
    page.locator('#plan-words').fill('30')
    page.locator('#plan-form button[type="submit"]').click()
    dashboard()
    assert page.get_by_role('progressbar', name='今日时长完成度', exact=True).get_attribute('aria-valuenow') == '36'
    assert page.get_by_role('progressbar', name='今日单词完成度', exact=True).get_attribute('aria-valuenow') == '80'
    page.locator('.progress-goals [data-route="plan"]').click()
    page.locator('#plan-minutes').fill('20')
    page.locator('#plan-words').fill('50')
    page.locator('#plan-form button[type="submit"]').click()
    dashboard()

    page.locator('.progress-goal-footer [data-action="progress-continue"]').click()
    expect(page.locator('#lesson-course')).to_contain_text('· 4/22')
    for field, value in zip(page.locator('.translation-blank').all(), ['good', 'afternoon']):
        field.fill(value)
    page.locator('#translation-submit').click()
    back()
    expect(page.locator('[data-progress-category="C01"] .progress-category-count')).to_have_text('23 / 136')
    assert saved()['days'][dates[-1]]['words'] == baseline['days'][dates[-1]]['words']
    page.locator('.progress-goal-footer [data-action="progress-continue"]').click()
    expect(page.locator('#lesson-course')).to_contain_text('· 5/22')
    back()
    page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));const date=Object.keys(s.days).sort().pop();s.days[date].seconds=1200;s.days[date].words=s.words.slice(0,50).map(w=>w.id);localStorage.setItem(key,JSON.stringify(s));}''')
    page.reload()
    page.locator('.progress-goal-footer [data-action="checkin"]').click()
    expect(page.locator('[data-progress-streak]')).to_have_text('4天')
    assert saved()['days'][dates[-1]]['checked'] is True
    for key in ['notes', 'settings', 'plan', 'challenges']:
        assert saved()[key] == baseline[key]
    for width in (1024, 1280, 1366, 1440, 1672, 1900):
        page.set_viewport_size({'width': width, 'height': 945})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert page.locator('.progress-category-row').count() == 8
        page.screenshot(path=f'/tmp/learning-progress-{width}.png', full_page=True)
    assert not errors, errors
    print('PASS: continue at saved question, grading updates category progress, repeat words are distinct, eligible check-in and responsive widths', flush=True)
    context.close()
    browser.close()
print('COMPLETE: learning progress dashboard passed', flush=True)
