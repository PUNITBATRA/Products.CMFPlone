# -*- coding: UTF-8 -*-
#
# Tests the CalendarPortlet View
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.CMFPlone.tests import PloneTestCase

from Products.CMFPlone.tests.PloneTestCase import FunctionalTestCase
from Products.CMFPlone.tests.PloneTestCase import default_user
from Products.CMFPlone.tests.PloneTestCase import default_password

from zope.app.testing.ztapi import provideUtility
from zope.app.testing.ztapi import unprovideUtility

from zope.i18n.simpletranslationdomain import SimpleTranslationDomain
from zope.i18n.interfaces import ITranslationDomain

from DateTime import DateTime

from Products.ATContentTypes.tests.utils import FakeRequestSession
from Products.CMFPlone.browser.interfaces import ICalendarPortlet
from Products.CMFPlone.browser.portlets.calendar import CalendarPortlet


class TestCalendarPortletView(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        self.url = self.portal.portal_url
        self.calendar = self.portal.portal_calendar
        self.now = DateTime()

    def testImplementsICalendarPortlet(self):
        """CalendarPortlet must implement ICalendarPortlet"""
        self.failUnless(ICalendarPortlet.implementedBy(CalendarPortlet))

    def testGetYearAndMonthToDisplay(self):
        """CalendarPortlet.getYearAndMonthToDisplay() must return the current
           year and month.
        """
        view = CalendarPortlet(self.portal, self.app.REQUEST)
        result = view.getYearAndMonthToDisplay()
        self.failUnlessEqual(result, (self.now.year(), self.now.month()))
        
    def testGetYearAndMonthToDisplayRequest(self):
        """CalendarPortlet.getYearAndMonthToDisplay() must return the year and
           month found in REQUEST variables.
        """
        self.app.REQUEST['year'] = 2005
        self.app.REQUEST['month'] = 7
        view = CalendarPortlet(self.portal, self.app.REQUEST)
        result = view.getYearAndMonthToDisplay()
        self.failUnlessEqual(result, (2005, 7))

    def testGetYearAndMonthToDisplaySession(self):
        """CalendarPortlet.getYearAndMonthToDisplay() must return the year and
           month found in SESSION variables if this is enables in the calendar
           tool.
        """
        usesession = self.calendar.getUseSession()
        self.app.REQUEST['SESSION'] = FakeRequestSession()
        self.app.REQUEST['SESSION']['calendar_year'] = 2004
        self.app.REQUEST['SESSION']['calendar_month'] = 6
        
        # Ignore the session variables and use the current date
        self.calendar.use_session = False
        view = CalendarPortlet(self.portal, self.app.REQUEST)
        result = view.getYearAndMonthToDisplay()
        self.failUnlessEqual(result, (self.now.year(), self.now.month()))
        
        # Use the session variables
        self.calendar.use_session = True
        view = CalendarPortlet(self.portal, self.app.REQUEST)
        result = view.getYearAndMonthToDisplay()
        self.failUnlessEqual(result, (2004, 6))
        
        # Restore the orginal value
        self.calendar.use_session = usesession

    def testGetPreviousMonth(self):
        view = CalendarPortlet(self.portal, self.app.REQUEST)
        result = view.getPreviousMonth(12, 2006)
        self.failUnlessEqual(result, DateTime(2006, 11, 1))
        
        result = view.getPreviousMonth(1, 2006)
        self.failUnlessEqual(result, DateTime(2005, 12, 1))

    def testGetNextMonth(self):
        view = CalendarPortlet(self.portal, self.app.REQUEST)
        result = view.getNextMonth(12, 2006)
        self.failUnlessEqual(result, DateTime(2007, 1, 1))
        
        result = view.getNextMonth(1, 2006)
        self.failUnlessEqual(result, DateTime(2006, 2, 1))

    def testIsToday(self):
        view = CalendarPortlet(self.portal, self.app.REQUEST)
        self.failUnless(view.isToday(self.now.day()))


class TestCalendarPortlet(PloneTestCase.FunctionalTestCase):

    def afterSetUp(self):
        self.portal_path = self.portal.absolute_url(1)
        self.basic_auth = '%s:%s' % (default_user, default_password)
        self.workflow = self.portal.portal_workflow

    def addEvent(self, id):
        self.portal.invokeFactory('Event', id)
        obj = getattr(self.portal, id)
        obj.setStartDate(DateTime())
        obj.setEndDate(DateTime()+1)
        obj.setTitle(u'\xf6hm %s title' % id)
        obj.setDescription(u'\xf6hm %s description' % id)
        # publish event
        self.workflow.doActionFor(obj, 'publish')

    def populateSite(self):
        self.setRoles(['Manager'])
        self.addEvent('event1')
        self.addEvent('event2')
        self.addEvent('event3')
        self.setRoles(['Member'])

    def testEmptyCalendar(self):
        response = self.publish(self.portal_path, self.basic_auth)

        self.assertEquals(response.getStatus(), 200)
        self.failUnless('id="thePloneCalendar"' in response.getBody())

    def testCalendarWithEvents(self):
        self.populateSite()
        response = self.publish(self.portal_path, self.basic_auth)

        self.assertEquals(response.getStatus(), 200)
        self.failUnless('id="thePloneCalendar"' in response.getBody())
        self.failUnless('event1' in response.getBody())
        self.failUnless('event2' in response.getBody())
        self.failUnless('event3' in response.getBody())

    def testLocalizedCalendarWithEvents(self):
        self.populateSite()

        # set up some messages to test the calendar date/time formatting
        messages = {
            ('ja', 'date_format_long'): unicode("${Y}年${m}月${d}日 ${H}時${M}分", "utf-8"),
            ('ja', 'date_format_short'): unicode("${Y}年${m}月${d}日", "utf-8")}
        dates = SimpleTranslationDomain('plone', messages)
        provideUtility(ITranslationDomain, dates, 'plone')

        response = self.publish(self.portal_path, self.basic_auth,
                                env={'HTTP_ACCEPT_LANGUAGE': 'ja'})
        self.assertEquals(response.getStatus(), 200)
        self.failUnless('id="thePloneCalendar"' in response.getBody())
        self.failUnless('event1' in response.getBody())
        self.failUnless('event2' in response.getBody())
        self.failUnless('event3' in response.getBody())

        # Clean up after ourselves
        unprovideUtility(ITranslationDomain, name='plone')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCalendarPortletView))
    suite.addTest(makeSuite(TestCalendarPortlet))
    return suite

if __name__ == '__main__':
    framework()
