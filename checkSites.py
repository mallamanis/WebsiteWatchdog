#!/usr/bin/env python

import csv
import httplib
import time
import smtplib
import urlparse
from email.mime.text import MIMEText

class WebsiteWatchdog(object):
  
  smtp_server = 'smtp.example.com'
  from_email = "watchdog@domain.com"
  to_email = "yourName@domain.com"
  
  config_file_path = '/path/to/sites'
  
  def get_site_to_check(self, filename):
    """
    Read from config file the sites and the checks to perform
    :param filename: the filename of the config file
    :return: a dict containing {siteUrl:[checks1, check2,...]}
    """
    csv_file = csv.reader(open(filename, 'r'), delimiter=";")
    
    sites={}
    for row in csv_file:
      if len(row) == 0:
        continue
      site_url = row[0]
      sites[site_url] = {"url":site_url}
      
      sites[site_url]["checks"] = []
      for check in row[1:]:
        sites[site_url]["checks"].append(check)
    return sites

  def check_sites_status(self, sites_to_check):
    """
    Check the status for each site in sites_to_check
    :param sites_to_check: the sites to check as a dict with the
    approriate checks {siteUrl:[checks1, check2,...]}
    :return: a dict {siteUrl:{error:True/False, reason:"a reason",...},...}
    """
    status = {}
    for site in sites_to_check:
      status[site] = self.check_site(site,sites_to_check[site]["checks"])
    return status

  def check_site(self, url, checks):
    """
    Check a single url given the checks. Checks HTTP Response Code
    and contents of page
    :return: a dict {error: True/False, reason:"some reason"}
    """
    parse = urlparse.urlparse(url)
    connection = httplib.HTTPConnection(parse.netloc)
    connection.request("GET", parse.path) #TODO: More complex in the future?
    response = connection.getresponse()
    
    if response.status != 200:
      error_explanation = str(response.status)+" "+response.reason
      return {"error":True, "reason":error_explanation}
    
    url_content = response.read()
    for check in checks:
      if url_content.find(check) == -1:
        error_explanation = "Failed to find '"+check+"' in page"
        return {"error":True, "reason":error_explanation}
    
    return {"error":False, "reason":"Site Seems Up"}
    
  def send_email(self, text):
    """
    Send email to about all failures, with the given text
    :param text: the text to send in the message
    """
    msg_text = MIMEText(text)
    msg_text['Subject'] = '[WebSite Watchdog] Failure'
    msg_text['From'] = self.from_email
    msg_text['To'] = self.to_email
    
    s = smtplib.SMTP(self.smtp_server)
    s.sendmail(self.from_email, [self.to_email], msg_text.as_string())
    s.quit()

  def notify_failures(self, results):
    msgText = "The following sites seemed to have a problem at "
    msgText += time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()) + "\n\n"
    
    has_error = False
    for site in results:
      if results[site]["error"]:
        has_error = True
        msgText += site + ": "+ results[site]["reason"] +"\n\n"
    
    if has_error:
      self.send_email(msgText)       
      
  def run_monitor(self):
    """
    Run the monitor once
    """
    data = self.get_site_to_check(self.config_file_path)
    results =  self.check_sites_status(data)
    self.notify_failures(results)


if __name__ == "__main__":
  a = WebsiteWatchdog()
  a.run_monitor()
